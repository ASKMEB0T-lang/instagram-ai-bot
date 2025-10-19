import openai
from instagrapi import Client
import time
import logging
import os

# إعداد التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class InstagramAIBot:
    def __init__(self):
        self.cl = Client()
        self.processed_messages = set()
        
    def login(self):
        """تسجيل الدخول إلى إنستغرام"""
        try:
            logger.info("🔐 جاري تسجيل الدخول إلى إنستغرام...")
            
            # الحصول على البيانات من Environment Variables
            username = os.getenv('INSTAGRAM_USERNAME')
            password = os.getenv('INSTAGRAM_PASSWORD')
            openai.api_key = os.getenv('OPENAI_API_KEY')
            
            if not username or not password:
                logger.error("❌ بيانات إنستغرام غير موجودة")
                return False
                
            # تسجيل الدخول
            self.cl.login(username, password)
            logger.info("✅ تم تسجيل الدخول بنجاح!")
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في التسجيل: {e}")
            return False
    
    def get_ai_response(self, message):
        """الحصول على رد من الذكاء الاصطناعي"""
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "أنت مساعد مفيد على إنستغرام. ارد بطريقة ودودة ومختصرة بالعربية."},
                    {"role": "user", "content": message}
                ],
                max_tokens=150,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"❌ خطأ في الذكاء الاصطناعي: {e}")
            return "شكراً لرسالتك! 🌟 كيف يمكنني مساعدتك؟"
    
    def check_and_reply(self):
        """فحص الرسائل والرد عليها"""
        try:
            # الحصول على المحادثات
            threads = self.cl.direct_threads(limit=15)
            message_count = 0
            
            for thread in threads:
                if hasattr(thread, 'unseen_count') and thread.unseen_count > 0:
                    logger.info(f"📩 وجد {thread.unseen_count} رسالة جديدة")
                    
                    # الحصول على الرسائل في هذه المحادثة
                    messages = self.cl.direct_messages(thread.id, limit=5)
                    
                    for msg in messages:
                        # التحقق من أن الرسالة جديدة
                        if (not hasattr(msg, 'is_seen') or not msg.is_seen) and msg.user_id != self.cl.user_id:
                            
                            message_id = f"{thread.id}_{msg.id}"
                            
                            if message_id not in self.processed_messages:
                                logger.info(f"💬 رسالة جديدة: {msg.text}")
                                
                                # توليد رد بالذكاء الاصطناعي
                                ai_response = self.get_ai_response(msg.text)
                                logger.info(f"🤖 الرد: {ai_response}")
                                
                                # إرسال الرد
                                self.cl.direct_send(ai_response, thread_ids=[thread.id])
                                logger.info("✅ تم إرسال الرد!")
                                
                                # وضع الرسالة كمعالجة
                                self.processed_messages.add(message_id)
                                message_count += 1
                                
                                # انتظار قصير بين الردود
                                time.sleep(3)
            
            if message_count > 0:
                logger.info(f"🎉 تم الرد على {message_count} رسالة")
            else:
                logger.info("🔍 لا توجد رسائل جديدة")
                
            return message_count
            
        except Exception as e:
            logger.error(f"⚠️ خطأ في فحص الرسائل: {e}")
            return 0
    
    def run(self):
        """الدورة الرئيسية للبوت"""
        if not self.login():
            logger.error("❌ لا يمكن متابعة التشغيل بسبب فشل التسجيل")
            return
        
        logger.info("🚀 البوت يعمل الآن! سيتم فحص الرسائل كل 30 ثانية...")
        logger.info("⏸️ لإيقاف البوت: اذهب لـ Render وأوقف الخدمة")
        
        try:
            while True:
                processed_count = self.check_and_reply()
                time.sleep(30)  # انتظر 30 ثانية بين كل فحص
                
        except KeyboardInterrupt:
            logger.info("⏹️ تم إيقاف البوت")
        except Exception as e:
            logger.error(f"💥 خطأ غير متوقع: {e}")

# نقطة الدخول الرئيسية
if __name__ == "__main__":
    logger.info("🤖 بدء تشغيل بوت إنستغرام الذكي...")
    bot = InstagramAIBot()
    bot.run()
