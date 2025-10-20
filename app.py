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

print("🚀 بدء تشغيل بوت إنستغرام AI مع Python 3.13...")

class InstagramBot:
    def __init__(self):
        self.cl = Client()
        self.cohere_api_key = os.getenv('COHERE_API_KEY', 'OLpDIVzr2jTSQwO32yqLiwUz3N1oaiBDm63Nck2Z')
        self.processed_messages = set()
        
        if not self.cohere_api_key:
            logger.error("❌ مفتاح Cohere API غير موجود")
            raise ValueError("Cohere API key is required")
    
    def login(self):
        """تسجيل الدخول إلى إنستغرام"""
        try:
            username = os.getenv('INSTAGRAM_USERNAME', 'askme.b0t')
            password = os.getenv('INSTAGRAM_PASSWORD', '123Aze@#')
            
            logger.info("🔐 جاري تسجيل الدخول...")
            
            # إعدادات متقدمة لتجنب الحظر
            self.cl.set_locale("en_US")
            self.cl.set_country("US")
            self.cl.set_timezone_offset(0)
            self.cl.delay_range = [2, 5]
            
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
            أنت مساعد عربي ذكي على إنستغرام. 
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
                "max_tokens": 70,
                "temperature": 0.8,
                "truncate": "END"
            }
            
            logger.info("🔄 جاري الاتصال بـ Cohere AI...")
            response = requests.post(url, json=data, headers=headers, timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                reply = result['generations'][0]['text'].strip()
                logger.info(f"🤖 تم توليد رد: {reply}")
                return reply
            else:
                logger.warning(f"⚠️ خطأ في API: {response.status_code}")
                return self.get_fallback_response(message)
                
        except Exception as e:
            logger.error(f"❌ خطأ في Cohere: {e}")
            return self.get_fallback_response(message)

    def get_fallback_response(self, message):
        """ردود احتياطية ذكية"""
        fallbacks_arabic = [
            "شكراً على رسالتك! 🌸 سأرد عليك قريباً",
            "أهلاً بك! 😊 رسالتك وصلت بنجاح",
            "مساؤك جميلة! 🌟 شكراً للتواصل معنا",
            "سعيد بتواصلك! 💫 شكراً للرسالة",
            "تم استلام رسالتك! 🌸 سأرد عليك عما قريب"
        ]
        
        fallbacks_english = [
            "Thanks for your message! 🌸 I'll reply soon",
            "Hello! 😊 Your message was received",
            "Great to hear from you! 🌟",
            "Thanks for reaching out! 💫",
            "Message received! 🌸 I'll get back to you"
        ]
        
        # تحديد اللغة تلقائياً
        if any(char in message for char in 'ابتثجحخدذرزسشصضطظعغفقكلمنهوي'):
            return random.choice(fallbacks_arabic)
        else:
            return random.choice(fallbacks_english)

    def check_and_reply_messages(self):
        """فحص الرسائل والرد عليها"""
        try:
            threads = self.cl.direct_threads(limit=8)
            replied_count = 0
            
            for thread in threads:
                if hasattr(thread, 'unseen_count') and thread.unseen_count > 0:
                    messages = self.cl.direct_messages(thread.id, limit=3)
                    
                    for msg in messages:
                        if (not hasattr(msg, 'is_seen') or not msg.is_seen) and msg.user_id != self.cl.user_id:
                            
                            msg_id = f"{thread.id}_{msg.id}"
                            
                            if msg_id not in self.processed_messages:
                                logger.info(f"📩 رسالة جديدة: {msg.text}")
                                
                                # توليد رد ذكي
                                reply = self.get_ai_response(msg.text)
                                
                                # إرسال الرد
                                self.cl.direct_send(reply, thread_ids=[thread.id])
                                logger.info("✅ تم إرسال الرد!")
                                
                                self.processed_messages.add(msg_id)
                                replied_count += 1
                                
                                # انتظار لتجنب rate limits
                                time.sleep(12)
            
            return replied_count
            
        except Exception as e:
            logger.error(f"❌ خطأ في فحص الرسائل: {e}")
            return 0

    def run(self):
        """تشغيل البوت الرئيسي"""
        if not self.login():
            logger.error("❌ لا يمكن بدء التشغيل بسبب فشل التسجيل")
            return
        
        logger.info("🤖 البوت يعمل الآن! جاري فحص الرسائل كل 25 ثانية...")
        
        while True:
            try:
                messages_handled = self.check_and_reply_messages()
                
                if messages_handled > 0:
                    logger.info(f"🎉 تم الرد على {messages_handled} رسالة")
                else:
                    logger.info("🔍 لا توجد رسائل جديدة...")
                
                time.sleep(25)  # انتظار 25 ثانية بين الدورات
                
            except Exception as e:
                logger.error(f"💥 خطأ غير متوقع: {e}")
                time.sleep(30)

if __name__ == "__main__":
    try:
        bot = InstagramBot()
        bot.run()
    except Exception as e:
        logger.error(f"💥 فشل تشغيل البوت: {e}")
        print(f"❌ فشل التشغيل: {e}")
