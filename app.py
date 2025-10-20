import os
import time
import logging
import random
import requests
import threading
from flask import Flask
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, ChallengeRequired
from dotenv import load_dotenv

# تحميل المتغيرات من .env
load_dotenv()

# إعداد تطبيق Flask
app = Flask(__name__)

# إعداد نظام التسجيل
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(
    level=LOG_LEVEL,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bot.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class InstagramAIBot:
    def __init__(self):
        self.cl = Client()
        self.username = os.getenv("INSTA_USERNAME")  # تم التعديل هنا
        self.password = os.getenv("INSTA_PASSWORD")  # تم التعديل هنا
        self.cohere_api_key = os.getenv("COHERE_API_KEY")
        self.rate_limit_delay = int(os.getenv("RATE_LIMIT_DELAY", "15"))  # تم التعديل هنا
        self.processed_messages = set()
        self.session_file = "session.json"
        self.is_running = False
        self.bot_thread = None
        
        # التحقق من وجود المتغيرات المطلوبة
        if not all([self.username, self.password, self.cohere_api_key]):
            logger.error("Missing required environment variables")
            raise ValueError("Please set all required environment variables in .env file")
        
        logger.info("Instagram AI Bot initialized successfully")
        self.apply_device_settings()

    def apply_device_settings(self):
        """إعداد إعدادات الجهاز لمحاكاة جهاز حقيقي"""
        try:
            user_agents = [
                "Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1",
                "Mozilla/5.0 (Linux; Android 11; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.120 Mobile Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            ]
            
            device_settings = {
                "user_agent": random.choice(user_agents),
                "device_settings": {
                    "app_version": "219.0.0.12.117",
                    "android_version": 29,
                    "android_release": "10.0",
                    "dpi": "480dpi",
                    "resolution": "1080x1920",
                    "manufacturer": "Samsung",
                    "device": "SM-G973F",
                    "model": "Galaxy S10",
                    "cpu": "qcom",
                    "version_code": "314665256"
                }
            }
            
            self.cl.set_settings(device_settings)
            logger.info("Device settings applied successfully")
        except Exception as e:
            logger.error(f"Error applying device settings: {e}")
            raise

    def login(self):
        """تسجيل الدخول إلى إنستغرام مع إدارة الجلسات"""
        try:
            if os.path.exists(self.session_file):
                logger.info("Loading existing session...")
                self.cl.load_settings(self.session_file)
                # محاولة استخدام الجلسة المحفوظة
                try:
                    self.cl.get_timeline_feed()
                    logger.info("Session is valid")
                    return True
                except LoginRequired:
                    logger.info("Session expired, logging in again...")
            
            logger.info("Performing new login...")
            self.cl.login(self.username, self.password)
            self.cl.dump_settings(self.session_file)
            logger.info("Login successful and session saved")
            return True
            
        except ChallengeRequired:
            logger.error("Instagram requires challenge verification")
            return False
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return False

    def generate_ai_reply(self, user_message):
        """إنشاء رد باستخدام Cohere AI"""
        try:
            if not user_message or len(user_message.strip()) == 0:
                return "مرحباً! كيف يمكنني مساعدتك؟"
            
            url = "https://api.cohere.ai/v1/generate"
            headers = {
                "Authorization": f"Bearer {self.cohere_api_key}",
                "Content-Type": "application/json"
            }
            
            prompt = f"""
            المستخدم قال: '{user_message}'
            ارد برد قصير وودود ومناسب لرسالة المستخدم. يجب أن يكون الرد باللغة العربية.
            الرد:
            """
            
            data = {
                "model": "command",
                "prompt": prompt,
                "max_tokens": 50,
                "temperature": 0.7,
                "stop_sequences": ["\n"]
            }
            
            response = requests.post(url, json=data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                reply = response.json()['generations'][0]['text'].strip()
                # تنظيف الرد من أي أحرف غير مرغوب فيها
                reply = reply.replace('"', '').replace("'", "").strip()
                return reply if reply else "شكراً على رسالتك! 😊"
            else:
                logger.warning(f"Cohere API returned status {response.status_code}")
                return "شكراً على رسالتك، سأرد عليك قريباً! 👍"
                
        except requests.exceptions.Timeout:
            logger.error("Cohere API timeout")
            return "شكراً على رسالتك! ⏰"
        except requests.exceptions.RequestException as e:
            logger.error(f"Cohere API request failed: {e}")
            return "أهلاً وسهلاً! 🌟"
        except Exception as e:
            logger.error(f"AI reply generation failed: {e}")
            return "مرحباً! كيف الحال؟ 😊"

    def check_messages(self):
        """فحص الرسائل الجديدة والرد عليها"""
        try:
            threads = self.cl.direct_threads(limit=10)
            new_messages_found = False
            
            for thread in threads:
                if thread.unseen_count > 0:
                    messages = self.cl.direct_messages(thread.id, limit=thread.unseen_count)
                    
                    for msg in messages:
                        if msg.user_id != self.cl.user_id:
                            msg_id = f"{thread.id}_{msg.id}"
                            
                            if msg_id not in self.processed_messages:
                                logger.info(f"New message from user {msg.user_id}: {msg.text}")
                                
                                # توليد رد AI
                                ai_reply = self.generate_ai_reply(msg.text)
                                
                                # إرسال الرد
                                self.cl.direct_send(ai_reply, thread_ids=[thread.id])
                                self.processed_messages.add(msg_id)
                                new_messages_found = True
                                
                                logger.info(f"Replied with: {ai_reply}")
                                
                                # استخدام RATE_LIMIT_DELAY من الإعدادات
                                time.sleep(self.rate_limit_delay)
            
            return new_messages_found
            
        except Exception as e:
            logger.error(f"Error checking messages: {e}")
            return False

    def cleanup_old_messages(self):
        """تنظيف الذاكرة من الرسائل القديمة"""
        if len(self.processed_messages) > 1000:
            # الاحتفاظ بـ 500 رسالة فقط
            self.processed_messages = set(list(self.processed_messages)[-500:])
            logger.info("Cleaned up old processed messages")

    def run_bot(self):
        """تشغيل البوت في حلقة منفصلة"""
        logger.info("Starting Instagram AI Bot...")
        
        if not self.login():
            logger.error("Login failed. Please check your credentials.")
            return

        logger.info("Bot is running and monitoring for new messages...")
        
        consecutive_errors = 0
        max_consecutive_errors = 5
        
        while self.is_running:
            try:
                messages_processed = self.check_messages()
                
                if messages_processed:
                    logger.info("Processed new messages successfully")
                    consecutive_errors = 0
                else:
                    logger.debug("No new messages found")
                
                # تنظيف الذاكرة دورياً
                self.cleanup_old_messages()
                
                # انتظار عشوائي قبل الفحص التالي
                sleep_time = random.randint(30, 60)
                logger.debug(f"Sleeping for {sleep_time} seconds")
                time.sleep(sleep_time)
                
            except Exception as e:
                consecutive_errors += 1
                logger.error(f"Unexpected error in main loop: {e}")
                
                if consecutive_errors >= max_consecutive_errors:
                    logger.error("Too many consecutive errors. Stopping bot.")
                    break
                
                # انتظار أطول عند الأخطاء
                time.sleep(120)

    def start(self):
        """بدء تشغيل البوت في thread منفصل"""
        if not self.is_running:
            self.is_running = True
            self.bot_thread = threading.Thread(target=self.run_bot)
            self.bot_thread.daemon = True
            self.bot_thread.start()
            logger.info("Bot thread started")

    def stop(self):
        """إيقاف البوت"""
        self.is_running = False
        logger.info("Bot stopped")

# إنشاء instance من البوت
bot = InstagramAIBot()

# routes لتطبيق Flask
@app.route('/')
def home():
    return {
        "status": "running",
        "bot": "Instagram AI Bot",
        "username": bot.username if bot else "Not initialized"
    }

@app.route('/start')
def start_bot():
    try:
        bot.start()
        return {"status": "success", "message": "Bot started successfully"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.route('/stop')
def stop_bot():
    try:
        bot.stop()
        return {"status": "success", "message": "Bot stopped successfully"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.route('/status')
def bot_status():
    return {
        "status": "running" if bot.is_running else "stopped",
        "username": bot.username,
        "processed_messages": len(bot.processed_messages)
    }

@app.route('/health')
def health_check():
    return {"status": "healthy", "timestamp": time.time()}

def main():
    """الدالة الرئيسية لتشغيل التطبيق"""
    try:
        # بدء البوت تلقائياً
        bot.start()
        
        # تشغيل خادم Flask
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port, debug=False)
        
    except Exception as e:
        logger.error(f"Failed to start application: {e}")
    finally:
        bot.stop()

if __name__ == "__main__":
    main()
