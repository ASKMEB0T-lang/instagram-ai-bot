import os
import time
import logging
import random
import requests
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, ChallengeRequired
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

print("🚀 بدء تشغيل بوت إنستغرام المتقدم...")

class AdvancedInstagramBot:
    def __init__(self):
        self.cl = Client()
        self.cohere_api_key = "OLpDIVzr2jTSQwO32yqLiwUz3N1oaiBDm63Nck2Z"
        self.processed_messages = set()
        
        # إعدادات متقدمة لمحاكاة المتصفح الحقيقي
        self.setup_advanced_settings()
    
    def setup_advanced_settings(self):
        """إعدادات متقدمة لتجنب الاكتشاف"""
        try:
            # إعدادات User-Agent عشوائية
            user_agents = [
                "Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.2 Mobile/15E148 Safari/604.1",
                "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Mobile Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
            ]
            
            self.cl.set_settings({
                "user_agent": random.choice(user_agents),
                "device_settings": {
                    "app_version": "219.0.0.12.117",
                    "android_version": 29,
                    "android_release": "10.0",
                    "dpi": "480dpi",
                    "resolution": "1080x1920",
                    "manufacturer": "Samsung",
                    "device": "SM-G973F",
                    "model": "Galaxy S10",
                    "cpu": "qcom",
                    "version_code": "314665256"
                },
                "country": "US",
                "locale": "en_US",
                "timezone_offset": -14400
            })
            
            logger.info("✅ الإعدادات المتقدمة جاهزة")
            
        except Exception as e:
            logger.error(f"❌ خطأ في الإعدادات: {e}")
    
    def smart_login(self):
        """تسجيل دخول ذكي مع معالجة الأخطاء المتقدمة"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                username = "askme.b0t"  # جرب حساب مختلف إذا لم يعمل
                password = "123Aze@#"
                
                logger.info(f"🔐 محاولة تسجيل الدخول {attempt + 1}/{max_retries}")
                
                # تأخير عشوائي بين المحاولات
                delay = random.randint(30, 90)
                logger.info(f"⏳ انتظار {delay} ثانية...")
                time.sleep(delay)
                
                # محاولة التسجيل
                self.cl.login(username, password)
                logger.info("✅ تم التسجيل بنجاح!")
                return True
                
            except ChallengeRequired as e:
                logger.warning("⚠️ إنستغرام يطلب تحقق إضافي")
                logger.info("🔑 يرجى التحقق من الحساب يدوياً أولاً")
                return False
                
            except LoginRequired as e:
                logger.error(f"❌ خطأ في التسجيل: {e}")
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 120  # انتظار متزايد
                    logger.info(f"🔄 إعادة المحاولة بعد {wait_time} ثانية...")
                    time.sleep(wait_time)
                else:
                    logger.error("❌ فشل جميع محاولات التسجيل")
                    return False
                    
            except Exception as e:
                logger.error(f"❌ خطأ غير متوقع: {e}")
                return False
        
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
            أنت مساعد ذكي على إنستغرام.
            المستخدم يقول: "{message}"
            
            ارد بطريقة:
            - ودودة وطبيعية
            - مختصرة (1-2 جملة)
            - استخدم إيموجي مناسب
            - باللغة العربية
            
            الرد:
            """
            
            data = {
                "model": "command",
                "prompt": prompt,
                "max_tokens": 60,
                "temperature": 0.7,
                "truncate": "END"
            }
            
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
        fallbacks = [
            "شكراً على رسالتك! 🌸 سأرد عليك قريباً",
            "أهلاً بك! 😊 رسالتك وصلت بنجاح",
            "مساؤك جميلة! 🌟 شكراً للتواصل معنا",
            "سعيد بتواصلك! 💫 شكراً للرسالة"
        ]
        return random.choice(fallbacks)
    
    def safe_check_messages(self):
        """فحص آمن للرسائل"""
        try:
            # تأخير عشوائي قبل الفحص
            time.sleep(random.randint(5, 15))
            
            threads = self.cl.direct_threads(limit=5)
            message_count = 0
            
            for thread in threads:
                try:
                    if hasattr(thread, 'unseen_count') and thread.unseen_count > 0:
                        messages = self.cl.direct_messages(thread.id, limit=3)
                        
                        for msg in messages:
                            if (not hasattr(msg, 'is_seen') or not msg.is_seen) and msg.user_id != self.cl.user_id:
                                
                                msg_id = f"{thread.id}_{msg.id}"
                                
                                if msg_id not in self.processed_messages:
                                    logger.info(f"📩 رسالة جديدة: {msg.text}")
                                    
                                    # توليد رد
                                    reply = self.get_ai_response(msg.text)
                                    
                                    # تأخير قبل الإرسال
                                    time.sleep(random.randint(10, 20))
                                    
                                    # إرسال الرد
                                    self.cl.direct_send(reply, thread_ids=[thread.id])
                                    logger.info("✅ تم إرسال الرد!")
                                    
                                    self.processed_messages.add(msg_id)
                                    message_count += 1
                                    
                                    # تأخير بين الردود
                                    time.sleep(random.randint(15, 30))
                except Exception as e:
                    logger.error(f"❌ خطأ في معالجة المحادثة: {e}")
                    continue
            
            return message_count
            
        except Exception as e:
            logger.error(f"❌ خطأ في فحص الرسائل: {e}")
            return 0
    
    def run(self):
        """تشغيل البوت الرئيسي"""
        logger.info("🚀 بدء تشغيل البوت المتقدم...")
        
        if not self.smart_login():
            logger.error("❌ لا يمكن بدء التشغيل بسبب فشل التسجيل")
            logger.info("💡 حاول: 1) إنشاء حساب جديد 2) التحقق يدوياً 3) الانتظار 24 ساعة")
            return
        
        logger.info("🤖 البوت يعمل الآن! جاري الفحص بذكاء...")
        
        cycle = 0
        while True:
            try:
                cycle += 1
                
                # تأخير عشوائي بين الدورات
                delay = random.randint(25, 45)
                logger.info(f"🔍 الدورة {cycle} - انتظار {delay} ثانية")
                time.sleep(delay)
                
                messages_handled = self.safe_check_messages()
                
                if messages_handled > 0:
                    logger.info(f"🎉 تم الرد على {messages_handled} رسالة")
                else:
                    logger.info(f"⏳ لا توجد رسائل جديدة - الدورة {cycle}")
                
            except Exception as e:
                logger.error(f"💥 خطأ غير متوقع: {e}")
                # انتظار طويل قبل إعادة المحاولة
                time.sleep(300)  # 5 دقائق

if __name__ == "__main__":
    try:
        bot = AdvancedInstagramBot()
        bot.run()
    except Exception as e:
        logger.error(f"💥 فشل تشغيل البوت: {e}")
