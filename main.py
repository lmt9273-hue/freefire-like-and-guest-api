import os
import json
import logging
import requests
import concurrent.futures
import telebot
from flask import Flask
from threading import Thread

# Flask Web Server (Render Port Fix ke liye)
app = Flask('')

@app.route('/')
def home():
    return "Bot is running live!"

def run():
    app.run(host='0.0.0.0', port=10000)

def keep_alive():
    t = Thread(target=run)
    t.start()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
BOT_TOKEN = os.getenv("BOT_TOKEN", "8868364202:AAFl-7nyZU4HBoD5OB4ADcM-54sQDe6G7IA").strip()

bot = telebot.TeleBot(BOT_TOKEN)

# Accounts JSON load karein
try:
    with open("accounts.json", "r") as f:
        FF_ACCOUNTS = json.load(f)
    logger.info(f"Loaded {len(FF_ACCOUNTS)} accounts successfully.")
except Exception as e:
    FF_ACCOUNTS = []
    logger.error(f"Failed to load accounts.json: {e}")

def send_like_account(account, target_uid, region):
    try:
        login_res = requests.post(
            "https://clientbp.ggservices.com/guest_login", 
            json={"account_id": account["account_id"], "password": account["password"]}, 
            timeout=5
        )
        if login_res.status_code == 200:
            token = login_res.json().get("token")
            headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/x-protobuf"}
            like_res = requests.post(
                "https://clientbp.ggservices.com/like_player", 
                json={"target_uid": int(target_uid), "region": region.upper()}, 
                headers=headers, 
                timeout=5
            )
            return like_res.status_code == 200
    except Exception:
        pass
    return False

@bot.message_handler(commands=['like'])
def handle_like(message):
    try:
        args = message.text.split()
        if len(args) < 3:
            bot.reply_to(message, "❌ **Usage:** `/like ind [UID]`", parse_mode="Markdown")
            return

        region = args[1].upper()
        uid = args[2]

        if not uid.isdigit():
            bot.reply_to(message, "❌ **UID mein sirf numbers honi chahiye!**")
            return

        status_msg = bot.reply_to(
            message, 
            f"🔄 **Connecting {len(FF_ACCOUNTS)} Accounts to Garena...**\n🆔 UID: `{uid}`", 
            parse_mode="Markdown"
        )

        successful_likes = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            results = [executor.submit(send_like_account, acc, uid, region) for acc in FF_ACCOUNTS]
            for future in concurrent.futures.as_completed(results):
                if future.result():
                    successful_likes += 1

        card_text = (
            f"🎉 **VIP LIKES DELIVERED!** 🚀\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🆔 **Target UID:** `{uid}`\n"
            f"🌐 **Region:** `{region}`\n"
            f"💖 **Likes Sent:** `+{successful_likes} Likes`\n"
            f"🤖 **Accounts Used:** `{len(FF_ACCOUNTS)}`\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"✅ **Status:** Direct In-Game Delivered!"
        )
        bot.edit_message_text(card_text, message.chat.id, status_msg.message_id, parse_mode="Markdown")

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

if __name__ == "__main__":
    keep_alive() # Port error fix karega
    bot.infinity_polling()
    
