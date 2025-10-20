import os
import time
import logging
import random
import requests
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, ChallengeRequired
from flask import Flask, jsonify

# ---------- إعداد اللوقينغ ----------
logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger("insta-bot")

# ---------- Flask app (لـ Render) ----------
app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Instagram AI Bot is running."

@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200

# ---------- الكلاس الخاص بالبوت ----------
class AdvancedInstagramBot:
    def __init__(self):
        self.cl = Client()
        self.session_file = os.path.join(os.getcwd(), "session.json")
        self.cohere_api_key = os.getenv("COHERE_API_KEY")  # اسم المتغير في Render
        self.processed_messages = set()
        self._stop = False
        self.setup_advanced_settings()

    def setup_advanced_settings(self):
        """إعدادات بسيطة للتخفيف من الكشف"""
        try:
            user_agents = [
                "Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X) AppleWebKit/605.1.15",
                "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko)",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko)"
            ]
            self.cl.set_settings({
                "user_agent": random.choice(user_agents),
                # يمكن توسيع device_settings هنا إن رغبت
            })
            logger.info("✅ إعدادات المتصفح تمت.")
        except Exception as e:
            logger.warning("⚠️ لم يتم تطبيق إعدادات متقدمة: %s", e)

    def load_session(self):
        if os.path.exists(self.session_file):
            try:
                self.cl.load_settings(self.session_file)
                logger.info("🔁 تم تحميل الجلسة من %s", self.session_file)
            except Exception as e:
                logger.warning("⚠️ فشل تحميل الجلسة: %s", e)

    def save_session(self):
        try:
            self.cl.dump_settings(self.session_file)
            logger.info("💾 تم حفظ الجلسة إلى %s", self.session_file)
        except Exception as e:
            logger.error("❌ فشل حفظ الجلسة: %s", e)

    def smart_login(self):
        """محاولة استخدام الجلسة المحفوظة، وإلا تسجيل الدخول عبر ENV"""
        # التحقق من وجود المتغيرات
        username = os.getenv("INSTA_USERNAME")
        password = os.getenv("INSTA_PASSWORD")

        if not username or not password:
            logger.error("❌ INSTA_USERNAME أو INSTA_PASSWORD غير مضبوطين في Environment variables.")
            return False

        # حاول استخدام الجلسة المحفوظة أولاً
        self.load_session()
        try:
            # اختبار صلاحية الجلسة عبر استدعاء بسيط
            self.cl.get_timeline_feed()
            logger.info("✅ الجلسة المحفوظة صالحة، لا حاجة لتسجيل الدخول.")
            return True
        except Exception:
            logger.info("ℹ️ الجلسة غير صالحة أو غير موجودة -> تسجيل دخول جديد")

        # تسجيل الدخول الفعلي
        attempts = 0
        max_attempts = 3
        while attempts < max_attempts:
            attempts += 1
            try:
                logger.info("🔐 محاولة تسجيل دخول %d/%d", attempts, max_attempts)
                # تأكد من أن username/password هما نصوص
                username = str(username)
                password = str(password)
                self.cl.login(username, password)
                self.save_session()
                logger.info("✅ تم تسجيل الدخول بنجاح.")
                return True

            except ChallengeRequired as e:
                logger.error("⚠️ تم طلب Challenge من إنستغرام (تحقق يدوي مطلوب). %s", e)
                return False

            except LoginRequired as e:
                logger.warning("❌ LoginRequired: %s", e)
                # تأخير تصاعدي بسيط قبل إعادة المحاولة
                time.sleep(5 * attempts)
                continue

            except Exception as e:
                logger.error("❌ حدث خطأ أثناء تسجيل الدخول: %s", e)
                time.sleep(5 * attempts)
                continue

        logger.error("❌ فشل تسجيل الدخول بعد %d محاولات", max_attempts)
        return False

    def get_ai_response(self, message: str) -> str:
        """استخدام Cohere (أو رد احتياطي عند الفشل)"""
        if not self.cohere_api_key:
            logger.warning("⚠️ COHERE_API_KEY غير موجودة — استخدام رد احتياطي.")
            return self.get_fallback_response(message)

        url = "https://api.cohere.ai/v1/generate"
        headers = {
            "Authorization": f"Bearer {self.cohere_api_key}",
            "Content-Type": "application/json"
        }
        prompt = f"أجب المستخدم بالعربية وبأسلوب ودود ومختصر. المستخدم: {message}"
        payload = {
            "model": "command",
            "prompt": prompt,
            "max_tokens": 60,
            "temperature": 0.7,
        }
        try:
            r = requests.post(url, json=payload, headers=headers, timeout=15)
            if r.status_code == 200:
                data = r.json()
                gen = data.get("generations", [])
                if gen:
                    text = gen[0].get("text", "").strip()
                    if text:
                        return text
            logger.warning("⚠️ Cohere returned status %s - using fallback", r.status_code)
        except Exception as e:
            logger.error("❌ خطأ عند استدعاء Cohere: %s", e)

        return self.get_fallback_response(message)

    def get_fallback_response(self, message: str) -> str:
        fallbacks = [
            "شكراً لرسالتك! 😊 سأرد عليك قريباً.",
            "أهلاً! رسالتك وصلت بنجاح 🌟",
            "سعيد بتواصلك! 💫"
        ]
        return random.choice(fallbacks)

    def safe_direct_threads(self, limit=5):
        """قراءة الخيوط مع إعادة محاولة بسيطة عند 429 أو أخطاء أخرى"""
        backoff = 1
        for _ in range(4):
            try:
                return self.cl.direct_threads(limit=limit)
            except Exception as e:
                msg = str(e).lower()
                if "429" in msg or "too many requests" in msg:
                    logger.warning("⚠️ Rate limited (429). الانتظار %s ثانية ثم إعادة المحاولة...", backoff)
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                logger.error("❌ خطأ عند جلب الخيوط: %s", e)
                return []
        return []

    def safe_direct_messages(self, thread_id, limit=3):
        backoff = 1
        for _ in range(4):
            try:
                return self.cl.direct_messages(thread_id, limit=limit)
            except Exception as e:
                msg = str(e).lower()
                if "429" in msg or "too many requests" in msg:
                    logger.warning("⚠️ Rate limited fetching messages. الانتظار %s ثانية...", backoff)
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                logger.error("❌ خطأ عند جلب الرسائل: %s", e)
                return []
        return []

    def safe_check_messages(self):
        """فحص رسائل الواردة والرد عليها"""
        try:
            threads = self.safe_direct_threads(limit=5)
            count = 0
            for thread in threads:
                try:
                    unseen = getattr(thread, "unseen_count", 0) or 0
                    if unseen > 0:
                        messages = self.safe_direct_messages(thread.id, limit=3)
                        for msg in messages:
                            # تحقق بسيط: تجاهل الرسائل من نفس البوت
                            if getattr(msg, "user_id", None) == getattr(self.cl, "user_id", None):
                                continue
                            text = getattr(msg, "text", None)
                            if not text:
                                continue
                            msg_key = f"{thread.id}_{getattr(msg, 'id', time.time())}"
                            if msg_key in self.processed_messages:
                                continue

                            logger.info("📩 رسالة جديدة: %s", text)
                            # توليد رد عن طريق AI
                            reply = self.get_ai_response(text)
                            # إرسال الرد مع محاولة ذكية عند فشل
                            try:
                                self.cl.direct_send(reply, thread_ids=[thread.id])
                                logger.info("✅ تم إرسال الرد إلى thread %s", thread.id)
                                self.processed_messages.add(msg_key)
                                count += 1
                                # تأخير صغير بعد إرسال الرد لتقليل احتمالية الحظر
                                time.sleep(random.randint(6, 12))
                            except Exception as e:
                                logger.error("❌ فشل إرسال الرد: %s", e)
                                # الاستمرار مع الرسائل الأخرى
                                continue
            return count
        except Exception as e:
            logger.error("❌ خطأ عام أثناء فحص الرسائل: %s", e)
            return 0

    def run(self):
        """حلقة التشغيل الأساسية للبوت"""
        if not self.smart_login():
            logger.error("❌ إيقاف التشغيل: تسجيل الدخول فشل.")
            return

        logger.info("🤖 البوت بدأ العمل الآن.")
        cycle = 0
        while not self._stop:
            cycle += 1
            try:
                logger.debug("🔁 دورة رقم %d", cycle)
                handled = self.safe_check_messages()
                if handled:
                    logger.info("🎉 ردّ على %d رسالة هذه الدورة", handled)
                else:
                    logger.debug("⏳ لا رسائل جديدة هذه الدورة")
                # انتظارات عشوائية قصيرة (لتقليل الكشف والحد من الحمل)
                time.sleep(random.randint(15, 30))
            except Exception as e:
                logger.error("💥 خطأ غير متوقع في حلقة البوت: %s", e)
                time.sleep(60)

    def stop(self):
        self._stop = True

# ---------- بدء البوت في Thread عند استيراد الملف ----------
bot_instance = AdvancedInstagramBot()

def start_bot_in_background():
    import threading
    t = threading.Thread(target=bot_instance.run, daemon=True, name="InstaBotThread")
    t.start()
    logger.info("🔁 بدء تشغيل البوت في الخلفية (Thread).")

# نبدأ البوت فقط مرة عند استيراد (مهم مع Gunicorn - تأكد من Workers = 1)
if os.getenv("START_BOT", "true").lower() in ("true", "1", "yes"):
    start_bot_in_background()
