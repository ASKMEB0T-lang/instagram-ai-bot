import os
import time
import logging
import requests
from instagrapi import Client
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("🚀 بدء تشغيل بوت إنستغرام AI...")

class InstagramBot:
    def __init__(self):
        self.cl = Client()
        self.cohere_api_key = os.getenv('COHERE_API_KEY')
    
    def login(self):
        try:
            username = os.getenv('INSTAGRAM_USERNAME')
            password = os.getenv('INSTAGRAM_PASSWORD')
            
            logger.info("🔐 جاري تسجيل الدخول...")
            self.cl.login(username, password)
            logger.info("✅ تم التسجيل بنجاح!")
            return True
        except Exception as e:
            logger.error(f"❌ خطأ في التسجيل: {e}")
            return False

    def get_ai_response(self, message):
        """الحصول على رد من Cohere AI"""
        try:
            url = "https://api.cohere.ai/v1/generate"
            headers = {
                "Authorization": f"Bearer {self.cohere_api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "command",
                "prompt": f"رد على هذه الرسالة بطريقة ودودة: {message}",
                "max_tokens": 50,
                "temperature": 0.7
            }
            
            response = requests.post(url, json=data, headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                return result['generations'][0]['text'].strip()
            else:
                return "شكراً على رسالتك! 🌸"
        except:
            return "أهلاً بك! 😊 كيف يمكنني مساعدتك؟"

    def check_messages(self):
        """فحص الرسائل الجديدة"""
        try:
            threads = self.cl.direct_threads(limit=5)
            for thread in threads:
                if hasattr(thread, 'unseen_count') and thread.unseen_count > 0:
                    logger.info("📩 توجد رسائل جديدة")
                    return True
            return False
        except Exception as e:
            logger.error(f"❌ خطأ في فحص الرسائل: {e}")
            return False

    def run(self):
        if self.login():
            logger.info("🤖 البوت يعمل الآن! جاري فحص الرسائل...")
            while True:
                try:
                    has_messages = self.check_messages()
                    if has_messages:
                        logger.info("🎯 تم اكتشاف رسائل جديدة")
                    time.sleep(30)
                except Exception as e:
                    logger.error(f"💥 خطأ: {e}")
                    time.sleep(60)

if __name__ == "__main__":
    bot = InstagramBot()
    bot.run()
