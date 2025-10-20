import os
import time
import logging
import requests
import random
import sys
from instagrapi import Client
from dotenv import load_dotenv

# عرض معلومات النظام
print(f"🐍 إصدار Python: {sys.version}")
print(f"🚀 بدء تشغيل بوت إنستغرام AI مع Python 3.13 و Pillow 11+")

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class InstagramBot:
    def __init__(self):
        self.cl = Client()
        self.cohere_api_key = "OLpDIVzr2jTSQwO32yqLiwUz3N1oaiBDm63Nck2Z"
        self.processed_messages = set()
        
        # التحقق من توفر الحزم المطلوبة
        try:
            from PIL import Image
            print("✅ Pillow/PIL متوفر ويعمل بنجاح")
        except ImportError as e:
            print(f"❌ خطأ في Pillow/PIL: {e}")
            raise
    
    def login(self):
        """تسجيل الدخول إلى إنستغرام"""
        try:
            username = "askme.b0t"
            password = "123Aze@#"
            
            logger.info("🔐 جاري تسجيل الدخول إلى إنستغرام...")
            
            # إعدادات متقدمة لتجنب الحظر
            settings = {
                "locale": "en_US",
                "country": "US", 
                "timezone_offset": 0,
                "delay_range": [2, 5]
            }
            
            self.cl.login(username, password, **settings)
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
                
            elif response.status_code == 429:
                logger.warning("⏳ تجاوز الحد المسموح في Cohere API")
                return self.get_fallback_response(message)
            else:
                logger.warning(f"⚠️ خطأ في API: {response.status_code}")
                return self.get_fallback_response(message)
                
        except Exception as e:
            logger.error(f"❌ خطأ في Cohere: {e}")
            return self.get_fallback_response(message)

    def get_fallback_response(self, message):
        """ردود احتياطية ذكية"""
        # اكتشاف اللغة تلقائياً
        arabic_chars = any(char in message for char in 'ابتثجحخدذرزسشصضطظعغفقكلمنهوي')
        
        if arabic_chars:
            responses = [
                "شكراً على رسالتك! 🌸 سأرد عليك قريباً",
                "أهلاً بك! 😊 رسالتك وصلت بنجاح",
                "مساؤك جميلة! 🌟 شكراً للتواصل معنا",
                "سعيد بتواصلك! 💫 شكراً للرسالة",
                "تم استلام رسالتك! 🌸 سأرد عليك عما قريب"
            ]
        else:
            responses = [
                "Thanks for your message! 🌸 I'll reply soon",
                "Hello! 😊 Your message was received",
                "Great to hear from you! 🌟",
                "Thanks for reaching out! 💫",
                "Message received! 🌸 I'll get back to you"
            ]
        
        return random.choice(responses)

    def check_and_reply_messages(self):
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
                                
                                # توليد رد ذكي
                                reply = self.get_ai_response(msg.text)
                                
                                # إرسال الرد
                                self.cl.direct_send(reply, thread_ids=[thread.id])
                                logger.info("✅ تم إرسال الرد!")
                                
                                self.processed_messages.add(msg_id)
                                replied_count += 1
                                
                                # انتظار لتجنب rate limits
                                time.sleep(15)
            
            return replied_count
            
        except Exception as e:
            logger.error(f"❌ خطأ في فحص الرسائل: {e}")
            return 0

    def run(self):
        """تشغيل البوت الرئيسي"""
        if not self.login():
            logger.error("❌ لا يمكن بدء التشغيل بسبب فشل التسجيل")
            return
        
        logger.info("🤖 البوت يعمل الآن! جاري فحص الرسائل كل 30 ثانية...")
        
        cycle = 0
        while True:
            try:
                cycle += 1
                messages_handled = self.check_and_reply_messages()
                
                if messages_handled > 0:
                    logger.info(f"🎉 تم الرد على {messages_handled} رسالة - الدورة {cycle}")
                else:
                    logger.info(f"🔍 لا توجد رسائل جديدة - الدورة {cycle}")
                
                time.sleep(30)
                
            except Exception as e:
                logger.error(f"💥 خطأ غير متوقع: {e}")
                time.sleep(60)

if __name__ == "__main__":
    try:
        bot = InstagramBot()
        bot.run()
    except Exception as e:
        logger.error(f"💥 فشل تشغيل البوت: {e}")
        print(f"❌ فشل التشغيل: {e}")
