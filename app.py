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

# إصدار التطبيق
__version__ = "1.0.0"

print(f"🚀 بدء تشغيل إنستغرام AI بوت - الإصدار {__version__}")

class InstagramBot:
    def __init__(self):
        self.cl = Client()
        self.processed_messages = set()
        self.cohere_api_key = os.getenv('COHERE_API_KEY')
        self.rate_limit_delay = 15  # 15 ثانية بين الطلبات
        
        if not self.cohere_api_key:
            logger.error("❌ COHERE_API_KEY not found in environment variables")
            raise ValueError("Cohere API key is required")
    
    def login(self):
        """تسجيل الدخول إلى إنستغرام"""
        try:
            username = os.getenv('INSTAGRAM_USERNAME')
            password = os.getenv('INSTAGRAM_PASSWORD')
            
            if not username or not password:
                logger.error("❌ Instagram credentials not found")
                return False
            
            logger.info("🔐 جاري تسجيل الدخول إلى إنستغرام...")
            
            # إعدادات إضافية لتجنب الحظر
            self.cl.set_locale("en_US")
            self.cl.set_country("US")
            self.cl.set_country_code(1)
            self.cl.set_timezone_offset(0)
            
            self.cl.login(username, password)
            logger.info("✅ تم تسجيل الدخول بنجاح!")
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
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
            
            prompt = f"""
            أنت مساعد عربي ذكي على إنستغرام. 
            المستخدم يقول: "{message}"
            
            ارد بطريقة:
            - ودودة وجذابة
            - مختصرة (1-2 جملة) 
            - مناسبة لوسائل التواصل الاجتماعي
            - باللغة العربية الفصحى
            - استخدم إيموجي مناسب
            
            الرد:
            """
            
            data = {
                "model": "command",
                "prompt": prompt,
                "max_tokens": 80,
                "temperature": 0.8,
                "k": 0,
                "stop_sequences": [],
                "return_likelihoods": "NONE"
            }
            
            logger.info("🔄 جاري الاتصال بـ Cohere AI...")
            response = requests.post(url, json=data, headers=headers, timeout=15)
            
            if response.status_code == 200:
                result = response.json()
                generated_text = result['generations'][0]['text'].strip()
                
                if generated_text and len(generated_text) > 10:
                    logger.info(f"✅ تم توليد رد ذكي: {generated_text}")
                    return generated_text
                else:
                    logger.warning("⚠️ الرد قصير جداً من Cohere")
                    return self.get_smart_fallback(message)
                    
            elif response.status_code == 429:
                logger.warning("⏳ تجاوز الحد المسموح (5 طلبات/دقيقة)")
                return self.get_smart_fallback(message)
            else:
                logger.warning(f"⚠️ استجابة Cohere: {response.status_code}")
                return self.get_smart_fallback(message)
                
        except Exception as e:
            logger.error(f"❌ خطأ في Cohere API: {e}")
            return self.get_smart_fallback(message)
    
    def get_smart_fallback(self, message):
        """ردود ذكية احتياطية"""
        message_lower = message.lower()
        
        smart_responses = {
            'مرحبا': [
                'أهلاً وسهلاً! 🌟 كيف يمكنني مساعدتك اليوم؟',
                'مرحباً بك! 😊 سعيد برؤية رسالتك',
                'أهلاً! 💫 أنا هنا لمساعدتك في أي شيء'
            ],
            'السلام عليكم': [
                'وعليكم السلام ورحمة الله وبركاته! 🌸',
                'السلام عليكم! أهلاً بك 🌟',
                'وعليكم السلام! كيف يمكنني مساعدتك؟ 😊'
            ],
            'اهلا': [
                'أهلاً بك! أنا بوت إنستغرام الذكي 🤖',
                'مرحباً! سعيد بتواصلك معنا 💫',
                'أهلاً! 🌟 شكراً لرسالتك الجميلة'
            ],
            'شكرا': [
                'العفو! 🤝 سعيد بخدمتك',
                'لا شكر على واجب! 🌸',
                'دمت بخير! 🌟'
            ],
            'كيف الحال': [
                'الحمد لله بخير! 😄 شكراً لسؤالك',
                'بخير الحمد لله! 🌸 كيف حالك أنت؟',
                'كل شيء ممتاز! 💫 شكراً لاهتمامك'
            ],
            'من انت': [
                'أنا مساعد ذكي للرد على رسائل إنستغرام تلقائياً! 🤖',
                'بوت ذكي تم برمجته لمساعدتك في الرد على الرسائل 🚀',
                'مساعدك الآلي على إنستغرام! 🌟'
            ],
            'مساعدة': [
                'يمكنني الرد على رسائلك تلقائياً! جرب أن ترسل لي أي رسالة 💬',
                'أنا هنا لمساعدتك! 💫 يمكنك مراسلتي بأي سؤال',
                'مساعدتك هي هدفنا! 🌸 ما الذي يمكنني فعله لك؟'
            ],
            'hello': [
                'Hello! 🌟 How can I help you today?',
                'Hi there! 😊 Nice to meet you!',
                'Hello! Welcome to our Instagram bot! 💫'
            ],
            'hi': [
                'Hi! 🌸 Great to see your message!',
                'Hello! 😊 How can I assist you?',
                'Hi there! 🌟 Thanks for reaching out!'
            ]
        }
        
        # البحث عن رد مناسب
        for key, responses in smart_responses.items():
            if key in message_lower:
                return random.choice(responses)
        
        # ردود سياقية ذكية
        if any(word in message_lower for word in ['احبك', 'حبيبي', 'عسل', 'جميل']):
            return random.choice([
                "شكراً لك! 😊 هذا لطف منك",
                "أنت رائع! 🌸 شكراً لطيب كلماتك",
                "هذا يجعلني سعيداً! 🌟"
            ])
        
        if any(word in message_lower for word in ['غاضب', 'زعلان', 'مستاء', 'مشكلة']):
            return random.choice([
                "أتمنى أن تتحسن أمورك قريباً! 🌸",
                "أنا هنا إذا أردت التحدث 🌟",
                "كل شيء سيكون على ما يرام! 💫"
            ])
        
        if '؟' in message or '?' in message:
            return random.choice([
                "سؤال ممتاز! 🤔 سأفكر في إجابة مناسبة لك",
                "أحب فضولك! 🌟 سأرد على سؤالك قريباً",
                "سؤال جميل! 💫 دعني أفكر في أفضل إجابة"
            ])
        
        # ردود عامة ذكية
        general_responses = [
            "شكراً لرسالتك! 🌟 سأرد عليك قريباً",
            "تم استلام رسالتك! 💫 شكراً للتواصل معنا",
            "أهلاً بك! 😊 رسالتك وصلت وسأرد عليك",
            "مساؤك جميلة! 🌸 شكراً لرسالتك",
            "سعيد بتواصلك! 🌟 شكراً للرسالة"
        ]
        
        return random.choice(general_responses)
    
    def check_messages(self):
        """فحص الرسائل والرد عليها"""
        try:
            threads = self.cl.direct_threads(limit=10)
            message_count = 0
            
            for thread in threads:
                if hasattr(thread, 'unseen_count') and thread.unseen_count > 0:
                    messages = self.cl.direct_messages(thread.id, limit=5)
                    
                    for msg in messages:
                        if (not hasattr(msg, 'is_seen') or not msg.is_seen) and msg.user_id != self.cl.user_id:
                            
                            msg_id = f"{thread.id}_{msg.id}"
                            
                            if msg_id not in self.processed_messages:
                                logger.info(f"📩 رسالة جديدة: {msg.text}")
                                
                                # استخدام Cohere AI للرد
                                response = self.get_cohere_response(msg.text)
                                logger.info(f"🤖 الرد: {response}")
                                
                                # إرسال الرد
                                self.cl.direct_send(response, thread_ids=[thread.id])
                                logger.info("✅ تم إرسال الرد!")
                                
                                self.processed_messages.add(msg_id)
                                message_count += 1
                                
                                # انتظار 12 ثانية بين الطلبات لتجنب تجاوز الحد (5/دقيقة)
                                time.sleep(self.rate_limit_delay)
            
            if message_count > 0:
                logger.info(f"🎉 تم الرد على {message_count} رسالة")
            else:
                logger.info("🔍 لا توجد رسائل جديدة")
                
            return message_count
            
        except Exception as e:
            logger.error(f"⚠️ خطأ في فحص الرسائل: {e}")
            return 0
    
    def run(self):
        """تشغيل البوت"""
        if not self.login():
            logger.error("❌ لا يمكن متابعة التشغيل بسبب فشل التسجيل")
            return
        
        logger.info("🚀 البوت يعمل الآن! سيتم فحص الرسائل كل 30 ثانية...")
        
        while True:
            try:
                processed = self.check_messages()
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
