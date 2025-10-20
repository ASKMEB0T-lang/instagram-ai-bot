import os
import time
import logging
import random
import requests
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, ChallengeRequired
import json
from flask import Flask

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)  # ✅ لإبقاء Render يعمل

@app.route("/")
def home():
    return "✅ Instagram Bot is Running on Render!"

print("🚀 بدء تشغيل بوت إنستغرام المتقدم...")

class AdvancedInstagramBot:
    def __init__(self):
        self.cl = Client()
        self.session_file = "session.json"
        self.cohere_api_key = os.getenv("COHERE_API_KEY", "YOUR_KEY")
        self.processed_messages = set()
        self.setup_advanced_settings()
        self.load_session()

    def setup_advanced_settings(self):
        try:
            self.cl.set_settings({})
            logger.info("✅ إعدادات الجهاز جاهزة")
        except Exception as e:
            logger.error(f"❌ خطأ في الإعدادات: {e}")

    def load_session(self):
        if os.path.exists(self.session_file):
            try:
                self.cl.load_settings(self.session_file)
                logger.info("🔁 تم تحميل جلسة Instagram من ملف session.json")
            except:
                logger.warning("⚠️ فشل تحميل الجلسة، سيتم تسجيل الدخول من جديد")

    def save_session(self):
        try:
            self.cl.dump_settings(self.session_file)
            logger.info("💾 تم حفظ الجلسة في session.json")
        except Exception as e:
            logger.error(f"❌ لم يتم حفظ الجلسة: {e}")

    def smart_login(self):
        try:
            self.cl.get_timeline_feed()  # هل الجلسة مازالت صالحة؟
            logger.info("✅ تم استخدام الجلسة المحفوظة دون تسجيل دخول")
            return True
        except:
            logger.info("🔐 جلسة غير صالحة، سيتم تسجيل الدخول الآن")

        try:
            username = os.getenv("IG_USERNAME")
            password = os.getenv("IG_PASSWORD")

            logger.info("🔐 تسجيل الدخول الآن دون تأخير طويل...")
            self.cl.login(username, password)
            self.save_session()
            logger.info("✅ تسجيل الدخول ناجح")
            return True
        except Exception as e:
            logger.error(f"❌ فشل تسجيل الدخول: {e}")
            return False

    def get_ai_response(self, message):
        try:
            url = "https://api.cohere.ai/v1/generate"
            headers = {
                "Authorization": f"Bearer {self.cohere_api_key}",
                "Content-Type": "application/json"
            }
            prompt = f"المستخدم: {message}\nالرد باختصار وبأسلوب ودود:"
            data = {"model": "command", "prompt": prompt, "max_tokens": 50}
            response = requests.post(url, json=data, headers=headers, timeout=10)

            if response.status_code == 200:
                return response.json()['generations'][0]['text'].strip()
            else:
                return "شكراً لتواصلك 😊"
        except:
            return "سعيد برسالتك! 🌟"

    def safe_check_messages(self):
        try:
            threads = self.cl.direct_threads(limit=5)
            for t in threads:
                if t.unseen_count > 0:
                    msgs = self.cl.direct_messages(t.id, limit=2)
                    for msg in msgs:
                        if msg.user_id != self.cl.user_id:
                            reply = self.get_ai_response(msg.text)
                            self.cl.direct_send(reply, thread_ids=[t.id])
                            logger.info(f"📩 رد: {reply}")
            return True
        except Exception as e:
            logger.error(f"❌ خطأ في قراءة الرسائل: {e}")
            return False

    def run(self):
        if not self.smart_login():
            return

        while True:
            self.safe_check_messages()
            time.sleep(20)

if __name__ == "__main__":
    bot = AdvancedInstagramBot()
    import threading
    threading.Thread(target=bot.run).start()

    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
