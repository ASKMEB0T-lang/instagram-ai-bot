import os
import requests
from flask import Flask, request, jsonify
import logging

# إعداد التسجيل
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# الحصول على الرموز من متغيرات البيئة
PAGE_ACCESS_TOKEN = os.getenv("PAGE_ACCESS_TOKEN")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN", "test123")

def send_facebook_message(recipient_id, message_text):
    """إرسال رسالة إلى المستخدم عبر فيسبوك"""
    try:
        url = "https://graph.facebook.com/v18.0/me/messages"
        params = {"access_token": PAGE_ACCESS_TOKEN}
        data = {
            "recipient": {"id": recipient_id},
            "message": {"text": message_text}
        }
        
        response = requests.post(url, json=data, params=params, timeout=10)
        
        if response.status_code == 200:
            logger.info(f"✅ تم إرسال الرسالة إلى {recipient_id}")
            return True
        else:
            logger.error(f"❌ فشل إرسال الرسالة: {response.json()}")
            return False
            
    except Exception as e:
        logger.error(f"خطأ في إرسال الرسالة: {e}")
        return False

def generate_response(user_message):
    """إنشاء رد ذكي على الرسالة"""
    user_message = user_message.lower().strip()
    
    if any(word in user_message for word in ["مرحباً", "اهلا", "السلام", "hello", "hi"]):
        return "أهلاً وسهلاً! 🌹 كيف يمكنني مساعدتك اليوم؟"
    
    elif any(word in user_message for word in ["كيف الحال", "اخبارك", "شونك"]):
        return "الحمد لله بخير! 😊 شكراً لسؤالك. كيف يمكنني مساعدتك؟"
    
    elif any(word in user_message for word in ["شكراً", "thanks", "مشكور"]):
        return "العفو! 😇 دائماً في خدمتك"
    
    elif any(word in user_message for word in ["مساعدة", "مساعده", "help"]):
        return "يمكنني مساعدتك في: الرد على استفساراتك، تقديم المعلومات، والتفاعل مع رسائلك! 💫"
    
    else:
        return f"شكراً على رسالتك! 📩 سأرد عليك قريباً. رسالتك: '{user_message}'"

@app.route('/')
def home():
    return jsonify({
        "status": "running",
        "service": "Facebook Messenger Bot",
        "message": "Bot is ready to receive messages!",
        "endpoints": {
            "webhook": "/webhook",
            "health": "/health"
        }
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "service": "facebook_bot"})

@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    try:
        if request.method == 'GET':
            hub_mode = request.args.get('hub.mode')
            hub_verify_token = request.args.get('hub.verify_token')
            hub_challenge = request.args.get('hub.challenge')
            
            logger.info(f"🔍 محاولة تحقق: mode={hub_mode}, token={hub_verify_token}")
            
            if hub_mode == 'subscribe' and hub_verify_token == VERIFY_TOKEN:
                logger.info("✅ تحقق الـ Webhook بنجاح!")
                return hub_challenge
            else:
                logger.error(f"❌ فشل التحقق! المتوقع: {VERIFY_TOKEN}, المستلم: {hub_verify_token}")
                return "Verification failed", 403
        
        elif request.method == 'POST':
            data = request.get_json()
            logger.info("📨 تم استلام بيانات من فيسبوك")
            
            if data.get('object') == 'page':
                for entry in data.get('entry', []):
                    for messaging_event in entry.get('messaging', []):
                        if messaging_event.get('message'):
                            sender_id = messaging_event['sender']['id']
                            message_text = messaging_event['message'].get('text', '')
                            
                            logger.info(f"💬 رسالة من {sender_id}: {message_text}")
                            
                            if message_text:
                                reply_text = generate_response(message_text)
                                success = send_facebook_message(sender_id, reply_text)
                                
                                if success:
                                    logger.info(f"✅ تم الرد على {sender_id}: {reply_text}")
                                else:
                                    logger.error(f"❌ فشل إرسال الرد إلى {sender_id}")
            
            return jsonify({"status": "ok"}), 200
            
    except Exception as e:
        logger.error(f"خطأ في webhook: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    logger.info("🚀 بدء تشغيل بوت فيسبوك ميسنجر...")
    app.run(host='0.0.0.0', port=5000, debug=False)
