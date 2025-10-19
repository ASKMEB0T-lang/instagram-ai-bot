import os
import time
import logging
from instagrapi import Client
import openai

# إعداد التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("🚀 بدء تشغيل بوت إنستغرام الذكي...")

class InstagramBot:
    def __init__(self):
        self.cl = Client()
        self.processed_messages = set()
        
    def login(self):
        """تسجيل الدخول إلى إنستغرام"""
        try:
            logger.info("🔐 جاري تسجيل الدخول إلى إنستغرام...")
            
            # استخدام البيانات التي أعطيتني إياها
            username = "askme.b0t"  # من البيانات
            password = "123Aze@#"   # من البيانات
            
            # إعداد OpenAI (سنستخدم ردوداً ذكية بسيطة أولاً)
            openai.api_key = "sk-demo-key-temporary"  # مؤقت
            
            self.cl.login(username, password)
            logger.info("✅ تم تسجيل الدخول بنجاح!")
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في التسجيل: {e}")
            return False
    
    def get_ai_response(self, message):
        """رد ذكي على الرسالة"""
        try:
            # في المستقبل سنستخدم OpenAI، لكن الآن سنستخدم ردوداً مبرمجة
            responses = {
                'مرحبا': 'أهلاً وسهلاً! 🌟 أنا بوت إنستغرام الذكي. كيف يمكنني مساعدتك؟',
                'السلام عليكم': 'وعليكم السلام ورحمة الله وبركاته! 😊',
                'اهلا': 'أهلاً بك! أنا هنا لمساعدتك.',
                'شكرا': 'العفو! سعيد بخدمتك. 🤝',
                'كيف الحال': 'الحمد لله بخير، شكراً لسؤالك! 😄',
                'من انت': 'أنا بوت ذكي تم برمجته للرد التلقائي على رسائل إنستغرام. 🤖',
                'مساعدة': 'يمكنني الرد على رسائلك تلقائياً. جرب أن ترسل لي أي رسالة! 💬',
                'hello': 'Hello! 🌟 I am an AI Instagram bot. How can I help you?',
                'hi': 'Hi there! 😊 Thanks for your message.'
            }
            
            # البحث عن رد مناسب
            msg_lower = message.lower()
            for key, response in responses.items():
                if key in msg_lower:
                    return response
            
            # رد افتراضي
            return "شكراً لرسالتك! 🌟 سأرد عليك بشكل مفصل قريباً."
            
        except Exception as e:
            return "شكراً لرسالتك! سأقوم بالرد قريباً."
    
    def check_messages(self):
        """فحص الرسائل الجديدة"""
        try:
            logger.info("🔍 جاري فحص الرسائل...")
            
            threads = self.cl.direct_threads(limit=10)
            message_count = 0
            
            for thread in threads:
                if hasattr(thread, 'unseen_count') and thread.unseen_count > 0:
                    logger.info(f"📩 وجد {thread.unseen_count} رسالة جديدة")
                    
                    messages = self.cl.direct_messages(thread.id, limit=5)
                    
                    for msg in messages:
                        if (not hasattr(msg, 'is_seen') or not msg.is_seen) and msg.user_id != self.cl.user_id:
                            
                            msg_id = f"{thread.id}_{msg.id}"
                            
                            if msg_id not in self.processed_messages:
                                logger.info(f"💬 رسالة جديدة: {msg.text}")
                                
                                # توليد رد
                                response = self.get_ai_response(msg.text)
                                logger.info(f"🤖 الرد: {response}")
                                
                                # إرسال الرد
                                self.cl.direct_send(response, thread_ids=[thread.id])
                                logger.info("✅ تم إرسال الرد!")
                                
                                self.processed_messages.add(msg_id)
                                message_count += 1
                                time.sleep(2)
            
            if message_count == 0:
                logger.info("🔍 لا توجد رسائل جديدة")
            else:
                logger.info(f"🎉 تم الرد على {message_count} رسالة")
                
            return message_count
            
        except Exception as e:
            logger.error(f"⚠️ خطأ في فحص الرسائل: {e}")
            return 0
    
    def run(self):
        """تشغيل البوت الرئيسي"""
        if not self.login():
            logger.error("❌ لا يمكن متابعة التشغيل")
            return
        
        logger.info("🚀 البوت يعمل الآن! سيتم فحص الرسائل كل 30 ثانية...")
        
        while True:
            try:
                self.check_messages()
                time.sleep(30)  # انتظر 30 ثانية
            except Exception as e:
                logger.error(f"💥 خطأ: {e}")
                time.sleep(60)

# بدء التشغيل
if __name__ == "__main__":
    bot = InstagramBot()
    bot.run()
