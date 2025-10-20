import os
import time
import logging
import random
import requests
from instagrapi import Client
from instagrapi.exceptions import LoginRequired, ChallengeRequired
from dotenv import load_dotenv

# تحميل المتغيرات من .env
load_dotenv()

# إعداد تسجيل الأحداث
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger(__name__)

class InstagramAIBot:
    def __init__(self):
        self.cl = Client()
        self.username = os.getenv("INSTAGRAM_USERNAME")
        self.password = os.getenv("INSTAGRAM_PASSWORD")
        self.cohere_api_key = os.getenv("COHERE_API_KEY")
        self.processed_messages = set()
        self.apply_device_settings()

    def apply_device_settings(self):
        try:
            user_agents = [
                "Mozilla/5.0 (iPhone; CPU iPhone OS 14_7_1)",
                "Mozilla/5.0 (Linux; Android 11; SM-G973F)",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
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
                }
            })
            logger.info("Device settings applied.")
        except Exception as e:
            logger.error(f"Error in device settings: {e}")

    def login(self):
        for attempt in range(3):
            try:
                logger.info(f"Login attempt {attempt + 1}/3")
                self.cl.login(self.username, self.password)
                logger.info("Login successful.")
                return True
            except ChallengeRequired:
                logger.warning("Instagram requires verification. Verify manually.")
                return False
            except Exception as e:
                logger.error(f"Login failed: {e}")
                time.sleep(10)
        return False

    def generate_ai_reply(self, user_message):
        try:
            url = "https://api.cohere.ai/v1/generate"
            headers = {
                "Authorization": f"Bearer {self.cohere_api_key}",
                "Content-Type": "application/json"
            }
            prompt = f"مستخدم قال: {user_message}\nرد بطريقة ذكية قصيرة وودية باللغة العربية:"
            data = {"model": "command", "prompt": prompt, "max_tokens": 60, "temperature": 0.7}
            response = requests.post(url, json=data, headers=headers, timeout=15)
            if response.status_code == 200:
                return response.json()['generations'][0]['text'].strip()
            return "تم استلام رسالتك."
        except:
            return "شكراً لتواصلك."

    def check_messages(self):
        try:
            time.sleep(random.randint(5, 10))
            threads = self.cl.direct_threads(limit=5)
            for thread in threads:
                if thread.unseen_count > 0:
                    messages = self.cl.direct_messages(thread.id, limit=2)
                    for msg in messages:
                        if msg.user_id != self.cl.user_id:
                            msg_id = f"{thread.id}_{msg.id}"
                            if msg_id not in self.processed_messages:
                                reply = self.generate_ai_reply(msg.text)
                                time.sleep(random.randint(5, 10))
                                self.cl.direct_send(reply, thread_ids=[thread.id])
                                logger.info(f"Replied to: {msg.text}")
                                self.processed_messages.add(msg_id)
        except Exception as e:
            logger.error(f"Error checking messages: {e}")

    def run(self):
        if not self.login():
            logger.error("Cannot start bot due to login failure.")
            return

        logger.info("Bot is running...")
        while True:
            try:
                self.check_messages()
                time.sleep(random.randint(20, 40))
            except Exception as e:
                logger.error(f"Bot crashed: {e}")
                time.sleep(60)

if __name__ == "__main__":
    bot = InstagramAIBot()
    bot.run()
