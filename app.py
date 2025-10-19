import os
import time
import logging
import requests
import random
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
        self.processed_messages = set()
    
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

    def get_ai_response(self, message):
        """الحصول على رد من Cohere AI"""
        try:
            url = "https://api.cohere.ai/v1/generate"
            headers = {
                "Authorization": f"Bearer {self.cohere_api_key}",
                "Content-Type": "application/json"
            }
            
            prompt = f"""
            أنت مساعد عربي ودود على إنستغرام.
            المستخدم يقول: "{message}"
            
            ارد بطريقة:
            - ودودة وجذابة
            - مختصرة (1-2 جملة)
            - استخدم إيموجي مناسب
            - باللغة العربية
            
            الرد:
            """
            
            data = {
                "model": "command",
                "prompt": prompt,
                "max_tokens": 60,
                "temperature": 0.7
            }
            
            response = requests.post(url, json=data, headers=headers, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                reply = result['generations'][0]['text'].strip()
                logger.info(f"🤖 رد AI: {reply}")
                return reply
            else:
                logger.warning(f"⚠️ خطأ في API: {response.status_code}")
                return self.get_fallback_response(message)
                
        except Exception as e:
            logger.error(f"❌ خطأ في Cohere: {e}")
            return self.get_fallback_response(message)

    def get_fallback_response(self, message):
        """ردود احتياطية ذكية"""
        fallbacks = [
            "شكراً على رسالتك! 🌸 سأرد عليك قريباً",
            "أهلاً بك! 😊 رسالتك وصلت بنجاح",
            "مساؤك جميلة! 🌟 شكراً للتواصل معنا",
            "سعيد بتواصلك! 💫 شكراً للرسالة",
            "تم استلام رسالتك! 🌸 سأرد عليك عما قريب"
        ]
        return random.choice(fallbacks)

    def check_and_reply_to_messages(self):
        """فحص الرسائل والرد عليها"""
        try:
            threads = self.cl.direct_threads(limit=10)
            replied_count = 0
            
            for thread in threads:
                if hasattr(thread, 'unseen_count') and thread.unseen_count > 0:
                    messages = self.cl.direct_messages(thread.id, limit=5)
                    
                    for msg in messages:
                        if (not hasattr(msg, 'is_seen') or not msg.is_seen) and msg.user_id != self.cl.user_id:
                            
                            msg_id = f"{thread.id}_{msg.id}"
                            
                            if msg_id not in self.processed_messages:
                                logger.info(f"📩 رسالة جديدة: {msg.text}")
                                
                                # توليد رد
                                reply = self.get_ai_response(msg.text)
                                
                                # إرسال الرد
                                self.cl.direct_send(reply, thread_ids=[thread.id])
                                logger.info("✅ تم إرسال الرد!")
                                
                                self.processed_messages.add(msg_id)
                                replied_count += 1
                                
                                # انتظار بين الردود
                                time.sleep(10)
            
            if replied_count > 0:
                logger.info(f"🎉 تم الرد على {replied_count} رسالة")
            else:
                logger.info("🔍 لا توجد رسائل جديدة")
                
            return replied_count
            
        except Exception as e:
            logger.error(f"❌ خطأ في فحص الرسائل: {e}")
            return 0

    def run(self):
        if not self.login():
            logger.error("❌ لا يمكن بدء التشغيل بسبب فشل التسجيل")
            return
        
        logger.info("🤖 البوت يعمل الآن! جاري فحص الرسائل كل 20 ثانية...")
        
        while True:
            try:
                messages_handled = self.check_and_reply_to_messages()
                time.sleep(20)  # انتظار 20 ثانية بين كل فحص
            except Exception as e:
                logger.error(f"💥 خطأ غير متوقع: {e}")
                time.sleep(30)

if __name__ == "__main__":
    bot = InstagramBot()
    bot.run()
