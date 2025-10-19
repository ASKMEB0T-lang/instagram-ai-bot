import os
import time
import logging
from instagrapi import Client
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("🚀 بدء تشغيل بوت إنستغرام AI...")

class InstagramBot:
    def __init__(self):
        self.cl = Client()
    
    def login(self):
        try:
            username = os.getenv('INSTAGRAM_USERNAME')
            password = os.getenv('INSTAGRAM_PASSWORD')
            
            if not username or not password:
                logger.error("❌ بيانات التسجيل غير موجودة")
                return False
            
            logger.info("🔐 جاري تسجيل الدخول...")
            self.cl.login(username, password)
            logger.info("✅ تم التسجيل بنجاح!")
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في التسجيل: {e}")
            return False
    
    def run(self):
        if self.login():
            logger.info("🤖 البوت يعمل الآن. جاري فحص الرسائل...")
            while True:
                try:
                    # كود فحص الرسائل سيضاف لاحقاً
                    time.sleep(30)
                except Exception as e:
                    logger.error(f"💥 خطأ: {e}")
                    time.sleep(60)

if __name__ == "__main__":
    bot = InstagramBot()
    bot.run()
