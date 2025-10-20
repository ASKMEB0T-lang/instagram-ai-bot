import os
import time
import logging
import random
import requests
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, ChallengeRequired
from flask import Flask

# تشغيل خادم ويب بسيط ليمنع Render من إيقاف التطبيق
app = Flask(__name__)

@app.route("/")
def home():
    return "✅ Instagram AI Bot is running on Render!"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
print("🚀 تشغيل بوت إنستغرام + Flask على Render...")

class AdvancedInstagramBot:
    def __init__(self):
        self.cl = Client()
        self.cohere_api_key = os.getenv("COHERE_API_KEY")
        self.processed_messages = set()
        self.setup_advanced_settings()

    def setup_advanced_settings(self):
        try:
            user_agents = [
                "Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1 like Mac OS X)",
                "Mozilla/5.0 (Linux; Android 10; SM-G973F)",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
            ]
            self.cl.set_settings({
                "user_agent": random.choice(user_agents),
                "device_settings": {
                    "app_version": "219.0.0.12.117",
                    "android_version": 29,
                    "android_release": "10.0"
                }
            })
            logger.info("✅ إعدادات تجنّب الحظر جاهزة")
        except Exception as e:
            logger.error(f"❌ خطأ في الإعدادات: {e}")

    def smart_login(self):
        username = os.getenv("INSTA_USERNAME")
        password = os.getenv("INSTA_PASSWORD")
        try:
            self.cl.login(username, password)
            logger.info("✅ تسجيل الدخول تم بنجاح")
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
            data = {
                "model": "command",
                "prompt": f"المستخدم قال: {message}\nرد بطريقة ودية وبجملة مختصرة:",
                "max_tokens": 50,
                "temperature": 0.7
            }
            response = requests.post(url, json=data, headers=headers, timeout=10)
            if response.status_code == 200:
                return response.json()['generations'][0]['text'].strip()
            return "شكراً لتواصلك! 😊"
        except:
            return "سعيد برسالتك! 💬"

    def check_messages(self):
        try:
            threads = self.cl.direct_threads(limit=5)
            for thread in threads:
                if thread.unseen_count > 0:
                    messages = self.cl.direct_messages(thread.id, limit=1)
                    for msg in messages:
                        if msg.user_id != self.cl.user_id:
                            reply = self.get_ai_response(msg.text)
                            self.cl.direct_send(reply, thread_ids=[thread.id])
                            logger.info(f"✅ رد على: {msg.text}")
        except Exception as e:
            logger.error(f"❌ خطأ الرسائل: {e}")

    def run(self):
        if not self.smart_login(): 
            return
        
        while True:
            self.check_messages()
            time.sleep(random.randint(20, 35))

if __name__ == "__main__":
    bot = AdvancedInstagramBot()
    
    # تشغيل Flask في Thread منفصل
    from threading import Thread
    Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)))).start()
    
    bot.run()
