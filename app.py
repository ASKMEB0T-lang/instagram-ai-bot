from flask import Flask, request
import os
import logging

app = Flask(__name__)

# إعداد التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "test123")

@app.route('/')
def home():
    return "✅ Facebook Bot is Running! Use /webhook for Facebook verification"

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    try:
        if request.method == 'GET':
            # التحقق من Webhook
            hub_mode = request.args.get('hub.mode')
            hub_verify_token = request.args.get('hub.verify_token')
            hub_challenge = request.args.get('hub.challenge')
            
            logger.info(f"🔍 Verification attempt: mode={hub_mode}, token={hub_verify_token}")
            
            if hub_mode == 'subscribe' and hub_verify_token == VERIFY_TOKEN:
                logger.info("✅ Webhook verification SUCCESS!")
                return hub_challenge
            else:
                logger.error(f"❌ Verification FAILED! Expected: {VERIFY_TOKEN}, Got: {hub_verify_token}")
                return "Verification failed", 403
        
        elif request.method == 'POST':
            # معالجة الرسائل الواردة
            data = request.get_json()
            logger.info("📨 Received message from Facebook")
            return "OK", 200
            
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return "Error", 500

if __name__ == '__main__':
    logger.info(f"🚀 Starting Facebook Bot with Verify Token: {VERIFY_TOKEN}")
    app.run(host='0.0.0.0', port=5000, debug=False)
