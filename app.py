import os
import time
import logging
import requests
import random
from instagrapi import Client
from dotenv import load_dotenv

# تحميل environment variables
load_dotenv()

# إعداد التسجيل
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

print("🚀 بدء تشغيل إنستغرام AI بوت...")

class InstagramBot:
    def __init__(self):
        self.cl = Client()
        self.processed_messages = set()
        self.cohere_api_key = os.getenv('COHERE_API_KEY')
        self.rate_limit_delay = 15
        
        if not self.cohere_api_key:
            logger.error("❌ COHERE_API_KEY not found")
            raise ValueError("Cohere API key is required")
    
    def login(self):
        """تسجيل الدخول إلى إنستغرام"""
        try:
            username = os.getenv('INSTAGRAM_USERNAME')
            password = os.getenv('INSTAGRAM_PASSWORD')
            
            if not username or not password:
                logger.error("❌ Instagram credentials not found")
                return False
            
            logger.info("🔐 جاري تسجيل الدخول...")
            self.cl.login(username, password)
            logger.info("✅ تم التسجيل بنجاح!")
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في التسجيل: {e}")
            return False
    
    def get_cohere_response(self, message):
        """الحصول على رد من Cohere AI"""
        try:
            url = "https://api.cohere.ai/v1/generate"
            headers = {
                "Authorization": f"Bearer {self.cohere_api_key}",
                "Content-Type": "application/json"
            }
            
            prompt = f"رد على هذه الرسالة بطريقة ودودة بالعربية: {message}"
            
            data = {
                "model": "command",
                "prompt": prompt,
                "max_tokens": 60,
                "temperature": 0.7
            }
            
            response = requests.post(url, json=data, headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                return result['generations'][0]['text'].strip()
            else:
                logger.warning(f"⚠️ Cohere error: {response.status_code}")
                return "شكراً على رسالتك! 🌸"
                
        except Exception as e:
            logger.error(f"❌ خطأ في Cohere: {e}")
            return "أهلاً بك! 😊"
    
    def check_messages(self):
        """فحص الرسائل"""
        try:
            threads = self.cl.direct_threads(limit=5)
            new_messages = 0
            
            for thread in threads:
                if hasattr(thread, 'unseen_count') and thread.unseen_count > 0:
                    messages = self.cl.direct_messages(thread.id, limit=3)
                    
                    for msg in messages:
                        if (not hasattr(msg, 'is_seen') or not msg.is_seen) and msg.user_id != self.cl.user_id:
                            msg_id = f"{thread.id}_{msg.id}"
                            
                            if msg_id not in self.processed_messages:
                                logger.info(f"📩 رسالة: {msg.text}")
                                reply = self.get_cohere_response(msg.text)
                                
                                self.cl.direct_send(reply, thread_ids=[thread.id])
                                logger.info("✅ تم الرد!")
                                
                                self.processed_messages.add(msg_id)
                                new_messages += 1
                                time.sleep(self.rate_limit_delay)
            
            return new_messages
            
        except Exception as e:
            logger.error(f"❌ خطأ في الرسائل: {e}")
            return 0
    
    def run(self):
        """تشغيل البوت"""
        if not self.login():
            return
        
        logger.info("🚀 البوت يعمل! جاري فحص الرسائل...")
        
        while True:
            try:
                self.check_messages()
                time.sleep(30)
            except Exception as e:
                logger.error(f"💥 خطأ: {e}")
                time.sleep(60)

if __name__ == "__main__":
    bot = InstagramBot()
    bot.run()
