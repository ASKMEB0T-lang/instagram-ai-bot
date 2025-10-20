import os
import time
import logging
import random
import requests
import json
from flask import Flask
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, ChallengeRequired
from dotenv import load_dotenv

# تحميل المتغيرات من .env
load_dotenv()

app = Flask(__name__)

# إعداد التسجيل
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class InstagramAIBot:
    def __init__(self):
        self.cl = Client()
        self.username = os.getenv("INSTA_USERNAME")
        self.password = os.getenv("INSTA_PASSWORD")
        self.cohere_api_key = os.getenv("COHERE_API_KEY")
        self.processed_messages = set()
        self.session_file = "session.json"
        
        if not all([self.username, self.password, self.cohere_api_key]):
            logger.error("Missing environment variables")
            raise ValueError("Set all required environment variables")
        
        self.setup_client()

    def setup_client(self):
        """إعداد عميل إنستغرام بإعدادات محسنة"""
        try:
            # تحميل جلسة موجودة أو إنشاء جديدة
            if os.path.exists(self.session_file):
                logger.info("Loading existing session...")
                self.cl.load_settings(self.session_file)
                # اختبار الجلسة
                try:
                    self.cl.get_timeline_feed()
                    logger.info("Session is valid")
                    return
                except LoginRequired:
                    logger.info("Session expired, creating new...")
                    os.remove(self.session_file)
            
            # إعدادات جهاز أكثر واقعية
            self.cl.set_settings({
                **self.cl.get_settings(),
                **{
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
                    },
                    "country": "US",
                    "locale": "en_US",
                    "timezone_offset": -14400,
                }
            })
            
            # تسجيل الدخول
            self.login()
            
        except Exception as e:
            logger.error(f"Setup error: {e}")
            raise

    def login(self):
        """تسجيل الدخول بمعدل أبطأ ومعالجة أفضل للأخطاء"""
        try:
            logger.info("Attempting login...")
            
            # تأخير عشوائي قبل التسجيل
            time.sleep(random.uniform(5, 15))
            
            # التسجيل
            self.cl.login(self.username, self.password)
            
            # حفظ الجلسة
            self.cl.dump_settings(self.session_file)
            logger.info("Login successful and session saved")
            
            # تأخير بعد التسجيل
            time.sleep(random.uniform(3, 8))
            
            return True
            
        except ChallengeRequired:
            logger.error("Challenge required - manual verification needed")
            return False
        except Exception as e:
            logger.error(f"Login failed: {e}")
            # إعادة تعيين الإعدادات عند الفشل
            if os.path.exists(self.session_file):
                os.remove(self.session_file)
            return False

    def safe_request(self, func, *args, **kwargs):
        """تنفيذ الطلبات بشكل آمن مع تجنب الحظر"""
        try:
            # تأخير عشوائي قبل كل طلب
            delay = random.uniform(10, 30)
            logger.debug(f"Waiting {delay:.1f}s before request")
            time.sleep(delay)
            
            result = func(*args, **kwargs)
            
            # تأخير عشوائي بعد كل طلب
            time.sleep(random.uniform(5, 15))
            
            return result
            
        except Exception as e:
            logger.error(f"Request failed: {e}")
            
            # إذا كان خطأ في التسجيل، حاول إعادة التسجيل
            if isinstance(e, LoginRequired):
                logger.info("Re-login required")
                self.login()
            
            return None

    def generate_ai_reply(self, user_message):
        """إنشاء رد AI مع معالجة أخطاء محسنة"""
        try:
            if not user_message or len(user_message.strip()) < 2:
                return "مرحباً! 😊"
            
            url = "https://api.cohere.ai/v1/generate"
            headers = {
                "Authorization": f"Bearer {self.cohere_api_key}",
                "Content-Type": "application/json"
            }
            
            prompt = f"رد على هذه الرسالة بطريقة ودودة وعربية: '{user_message}'"
            
            data = {
                "model": "command",
                "prompt": prompt,
                "max_tokens": 40,
                "temperature": 0.7,
                "stop_sequences": ["\n"]
            }
            
            response = requests.post(url, json=data, headers=headers, timeout=20)
            
            if response.status_code == 200:
                reply = response.json()['generations'][0]['text'].strip()
                return reply if reply and len(reply) > 2 else "شكراً على رسالتك! 🌟"
            else:
                logger.warning(f"Cohere API error: {response.status_code}")
                return "أهلاً! شكراً للتواصل معي 👍"
                
        except Exception as e:
            logger.error(f"AI reply error: {e}")
            return "مرحباً! كيف يمكنني مساعدتك؟ 😊"

    def check_messages(self):
        """فحص الرسائل بمعدل آمن"""
        try:
            # استخدام الطلب الآمن
            threads = self.safe_request(self.cl.direct_threads, limit=5)
            if not threads:
                return False
            
            new_messages = False
            
            for thread in threads:
                if thread.unseen_count > 0:
                    messages = self.safe_request(self.cl.direct_messages, thread.id, limit=thread.unseen_count)
                    if not messages:
                        continue
                    
                    for msg in messages:
                        if msg.user_id != self.cl.user_id:
                            msg_id = f"{thread.id}_{msg.id}"
                            
                            if msg_id not in self.processed_messages:
                                logger.info(f"New message: {msg.text}")
                                
                                # توليد الرد
                                reply = self.generate_ai_reply(msg.text)
                                
                                # إرسال الرد بشكل آمن
                                self.safe_request(self.cl.direct_send, reply, thread_ids=[thread.id])
                                
                                self.processed_messages.add(msg_id)
                                new_messages = True
                                logger.info(f"Replied: {reply}")
            
            return new_messages
            
        except Exception as e:
            logger.error(f"Message check error: {e}")
            return False

    def run_bot_loop(self):
        """الحلقة الرئيسية للبوت بمعدلات آمنة"""
        logger.info("Starting bot loop...")
        
        if not self.login():
            logger.error("Initial login failed - stopping bot")
            return
        
        error_count = 0
        max_errors = 3
        
        while True:
            try:
                has_messages = self.check_messages()
                
                if has_messages:
                    logger.info("Processed messages successfully")
                    error_count = 0
                else:
                    logger.debug("No new messages")
                
                # انتظار طويل بين الدورات
                sleep_time = random.randint(45, 90)
                logger.debug(f"Next check in {sleep_time}s")
                time.sleep(sleep_time)
                
            except Exception as e:
                error_count += 1
                logger.error(f"Bot loop error #{error_count}: {e}")
                
                if error_count >= max_errors:
                    logger.error("Too many errors - stopping bot")
                    break
                
                # انتظار طويل عند الأخطاء
                time.sleep(120)

# تهيئة البوت
bot = InstagramAIBot()

# routes لـ Flask
@app.route('/')
def home():
    return {"status": "running", "service": "Instagram AI Bot"}

@app.route('/health')
def health():
    return {"status": "healthy", "timestamp": time.time()}

@app.route('/start')
def start_bot():
    import threading
    thread = threading.Thread(target=bot.run_bot_loop, daemon=True)
    thread.start()
    return {"status": "started", "message": "Bot started in background"}

def main():
    """الدالة الرئيسية"""
    try:
        # بدء البوت في الخلفية
        import threading
        bot_thread = threading.Thread(target=bot.run_bot_loop, daemon=True)
        bot_thread.start()
        
        # تشغيل Flask
        port = int(os.environ.get('PORT', 5000))
        app.run(host='0.0.0.0', port=port, debug=False)
        
    except Exception as e:
        logger.error(f"Application failed: {e}")

if __name__ == "__main__":
    main()
