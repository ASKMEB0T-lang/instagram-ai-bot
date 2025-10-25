import os
import time
import logging
import random
import requests
from flask import Flask
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, ChallengeRequired
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class FixedInstagramBot:
    def __init__(self):
        self.cl = Client()
        self.username = os.getenv("INSTA_USERNAME")
        self.password = os.getenv("INSTA_PASSWORD")
        self.cohere_api_key = os.getenv("COHERE_API_KEY")
        self.processed_messages = set()
        self.session_file = "ig_session.json"
        self.is_logged_in = False
        
        if not all([self.username, self.password, self.cohere_api_key]):
            logger.error("Missing environment variables")
            raise ValueError("Please check .env file")

    def safe_login(self):
        """تسجيل دخول آمن مع تجنب التضارب"""
        try:
            # تأخير عشوائي طويل قبل المحاولة
            delay = random.randint(30, 60)
            logger.info(f"Waiting {delay} seconds before login attempt...")
            time.sleep(delay)
            
            # محاولة استخدام جلسة موجودة أولاً
            if os.path.exists(self.session_file):
                logger.info("Found existing session, loading...")
                self.cl.load_settings(self.session_file)
                
                # اختبار الجلسة
                try:
                    user_info = self.cl.account_info()
                    logger.info(f"✅ Session valid for: {user_info.username}")
                    self.is_logged_in = True
                    return True
                except LoginRequired:
                    logger.info("Session expired, need new login")
            
            # تسجيل دخول جديد
            logger.info("Starting new login process...")
            
            # إعدادات جهاز فريدة
            settings = {
                "user_agent": "Instagram 219.0.0.12.117 Android (29/10; 480dpi; 1080x1920; samsung; SM-G973F; beyond1; exynos9820; en_US; 314665256)",
                "device_settings": {
                    "app_version": "219.0.0.12.117",
                    "android_version": 29,
                    "android_release": "10.0",
                    "dpi": "480dpi",
                    "resolution": "1080x1920",
                    "manufacturer": "samsung",
                    "device": "SM-G973F",
                    "model": "beyond1", 
                    "cpu": "exynos9820",
                    "version_code": "314665256"
                }
            }
            
            self.cl.set_settings(settings)
            
            # تسجيل الدخول
            self.cl.login(self.username, self.password)
            self.cl.dump_settings(self.session_file)
            
            self.is_logged_in = True
            logger.info("✅ Login successful!")
            return True
            
        except ChallengeRequired as e:
            logger.error(f"❌ Challenge required: {e}")
            logger.info("💡 Please login manually first and approve the session")
            return False
        except Exception as e:
            logger.error(f"❌ Login failed: {e}")
            return False

    def generate_ai_reply(self, user_message):
        """إنشاء رد باستخدام Cohere AI"""
        try:
            if not user_message or len(user_message.strip()) < 1:
                return "مرحباً! 😊"
            
            url = "https://api.cohere.ai/v1/generate"
            headers = {
                "Authorization": f"Bearer {self.cohere_api_key}",
                "Content-Type": "application/json"
            }
            
            prompt = f"رد على '{user_message}' برد عربي قصير وودود:"
            
            data = {
                "model": "command",
                "prompt": prompt,
                "max_tokens": 50,
                "temperature": 0.7
            }
            
            response = requests.post(url, json=data, headers=headers, timeout=15)
            
            if response.status_code == 200:
                reply = response.json()['generations'][0]['text'].strip()
                return reply if reply else "شكراً على رسالتك! 🌟"
            else:
                return "أهلاً وسهلاً! 🌸"
                
        except Exception:
            return "مرحباً! 🌺"

    def check_and_reply_to_messages(self):
        """فحص الرسائل والرد عليها"""
        if not self.is_logged_in:
            logger.warning("Not logged in, skipping message check")
            return False
            
        try:
            # تأخير قبل فحص الرسائل
            time.sleep(random.randint(20, 40))
            
            logger.info("Checking for new messages...")
            threads = self.cl.direct_threads(limit=5)
            
            if not threads:
                logger.info("No threads found")
                return False
            
            new_replies = 0
            
            for thread in threads:
                try:
                    # فحص الرسائل غير المقروءة فقط
                    if thread.unseen_count > 0:
                        logger.info(f"Found {thread.unseen_count} unseen messages in thread")
                        
                        messages = self.cl.direct_messages(thread.id, limit=thread.unseen_count)
                        
                        for msg in messages:
                            # التأكد من أن الرسالة ليست من البوت
                            if msg.user_id != self.cl.user_id:
                                msg_id = f"{thread.id}_{msg.id}"
                                
                                if msg_id not in self.processed_messages:
                                    logger.info(f"📨 New message: {msg.text}")
                                    
                                    # توليد الرد
                                    ai_reply = self.generate_ai_reply(msg.text)
                                    
                                    # تأخير قبل الإرسال
                                    time.sleep(random.randint(10, 20))
                                    
                                    # إرسال الرد
                                    self.cl.direct_send(ai_reply, thread_ids=[thread.id])
                                    
                                    self.processed_messages.add(msg_id)
                                    new_replies += 1
                                    
                                    logger.info(f"📤 Replied: {ai_reply}")
                                    
                                    # تأخير بين الردود
                                    time.sleep(random.randint(15, 25))
                except Exception as e:
                    logger.error(f"Error processing thread: {e}")
                    continue
            
            if new_replies > 0:
                logger.info(f"✅ Successfully sent {new_replies} replies")
            else:
                logger.info("No new messages to reply to")
                
            return new_replies > 0
            
        except Exception as e:
            logger.error(f"Error in message check: {e}")
            self.is_logged_in = False  # إعادة التعيين للتحقق لاحقاً
            return False

    def run_bot(self):
        """تشغيل البوت الرئيسي"""
        logger.info("🚀 Starting Instagram AI Bot...")
        
        # محاولة تسجيل الدخول الأولى
        if not self.safe_login():
            logger.error("❌ Initial login failed - bot cannot start")
            return

        logger.info("🤖 Bot is running and monitoring messages...")
        
        error_count = 0
        max_errors = 3
        
        while True:
            try:
                # فحص الرسائل
                success = self.check_and_reply_to_messages()
                
                if success:
                    error_count = 0
                    logger.info("✅ Message check completed successfully")
                else:
                    logger.info("ℹ️ No activity this cycle")
                
                # انتظار طويل بين الدورات (2-3 دقائق)
                sleep_time = random.randint(120, 180)
                logger.info(f"💤 Sleeping for {sleep_time} seconds...")
                time.sleep(sleep_time)
                
            except Exception as e:
                error_count += 1
                logger.error(f"❌ Bot error #{error_count}: {e}")
                
                if error_count >= max_errors:
                    logger.error("🛑 Too many errors, stopping bot")
                    break
                
                # انتظار طويل عند الأخطاء
                time.sleep(300)  # 5 دقائق

# إنشاء البوت
bot = FixedInstagramBot()

# Routes
@app.route('/')
def home():
    return {
        "status": "running",
        "service": "Instagram AI Bot",
        "logged_in": bot.is_logged_in,
        "message": "Service is active - Bot monitors messages automatically"
    }

@app.route('/health')
def health():
    return {
        "status": "healthy", 
        "logged_in": bot.is_logged_in,
        "timestamp": time.time()
    }

@app.route('/start')
def start_bot():
    import threading
    if not bot.is_logged_in:
        # محاولة تسجيل الدخول أولاً
        if bot.safe_login():
            thread = threading.Thread(target=bot.run_bot, daemon=True)
            thread.start()
            return {"status": "started", "message": "Bot started successfully"}
        else:
            return {"status": "error", "message": "Login failed - cannot start bot"}
    else:
        thread = threading.Thread(target=bot.run_bot, daemon=True)
        thread.start()
        return {"status": "started", "message": "Bot started successfully"}

@app.route('/login-status')
def login_status():
    return {
        "logged_in": bot.is_logged_in,
        "username": bot.username if bot.is_logged_in else "Not logged in"
    }

def main():
    port = int(os.environ.get('PORT', 5000))
    
    # بدء البوت تلقائياً في الخلفية
    import threading
    bot_thread = threading.Thread(target=bot.run_bot, daemon=True)
    bot_thread.start()
    
    # تشغيل Flask
    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == "__main__":
    main()
