import os
import json
import logging
import requests
import concurrent.futures
import telebot
from flask import Flask
from threading import Thread

# Render Port Fix Web Server
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

BOT_TOKEN = os.getenv("BOT_TOKEN", "8868364202:AAFl-7nyZU4HBoD5OB4ADcM-54sQDe6G7IA").strip()
bot = telebot.TeleBot(BOT_TOKEN)

try:
    with open("accounts.json", "r") as f:
        FF_ACCOUNTS = json.load(f)
    logger.info(f"Loaded {len(FF_ACCOUNTS)} accounts.")
except Exception as e:
    FF_ACCOUNTS = []
    logger.error(f"Accounts load error: {e}")

def send_like_account(account, target_uid, region):
    # Regional Direct Endpoints to Bypass Level Restrictions
    urls = [
        "https://clientbp.ggservices.com/like_player",
        "https://clientbp.ind.ggservices.com/like_player",
        "https://freefire-like-api.vercel.app/like"
    ]
    
    headers = {
        "User-Agent": "Dalvik/2.1.0 (Linux; U; Android 11; M2007J20CI Build/RKQ1.200826.002)",
        "Content-Type": "application/json"
    }
    
    payload = {
        "account_id": account.get("account_id"),
        "password": account.get("password"),
        "target_uid": str(target_uid),
        "region": region.lower()
    }
    
    for url in urls:
        try:
            res = requests.post(url, json=payload, headers=headers, timeout=4)
            if res.status_code == 200:
                data = res.json()
                if data.get("status") == "success" or data.get("code") == 200:
                    return True
        except Exception:
            continue
            
    # Direct Guest Token Fallback
    try:
        login_res = requests.post(
            "https://clientbp.ggservices.com/guest_login", 
            json={"account_id": account.get("account_id"), "password": account.get("password")}, 
            timeout=3
        )
        if login_res.status_code == 200:
            token = login_res.json().get("token")
            auth_headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/x-protobuf"}
            like_res = requests.post(
                "https://clientbp.ggservices.com/like_player", 
                json={"target_uid": int(target_uid), "region": region.upper()}, 
                headers=auth_headers, 
                timeout=3
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
            bot.reply_to(message, "❌ **UID numerical honi chahiye!**")
            return

        status_msg = bot.reply_to(
            message, 
            f"⚡ **Bypassing Garena Server Limits...**\n🆔 Target UID: `{uid}`", 
            parse_mode="Markdown"
        )

        successful_likes = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
            results = [executor.submit(send_like_account, acc, uid, region) for acc in FF_ACCOUNTS]
            for future in concurrent.futures.as_completed(results):
                if future.result():
                    successful_likes += 1

        card_text = (
            f"🚀 **BOOSTED LIKES DELIVERED!** 🎉\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🆔 **Target UID:** `{uid}`\n"
            f"🌐 **Region:** `{region}`\n"
            f"💖 **Likes Added:** `+{successful_likes} Likes`\n"
            f"🤖 **Accounts Processed:** `{len(FF_ACCOUNTS)}`\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"✅ **Status:** Direct Game Injected!"
        )
        bot.edit_message_text(card_text, message.chat.id, status_msg.message_id, parse_mode="Markdown")

    except Exception as e:
        bot.reply_to(message, f"❌ Error: {e}")

if __name__ == "__main__":
    keep_alive()
    bot.infinity_polling()
