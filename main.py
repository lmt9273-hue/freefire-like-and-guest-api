import threading
import time
import os
import sqlite3
from datetime import datetime, timedelta
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import logging
import requests
from flask import Flask

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BOT_TOKEN = "8868364202:AAFhI1n-PJ-vS0x_OWZlpwN0k7m4GSSLRLI"
REQUIRED_CHANNELS = ["@hacklinkpc"]
OWNER_ID = 7125817223
OWNER_USERNAME = "rohit2848"
UPI_ID = "7605900368@fam"

GPLINKS_API_KEY = "B127680908b90e463b9216880b34fb36e0a6a9c6"
TARGET_URL = "https://t.me/hacklinkpc"

QR_CODE_URL = "https://raw.githubusercontent.com/lmt9273-hue/freefire-like-and-guest-api/refs/heads/main/photo_2026-08-23_10-14-11.jpg"

bot = telebot.TeleBot(BOT_TOKEN)

BOT_CONTROL_FILE = "bot_stopped.lock"

def init_db():
    conn = sqlite3.connect('bot_data.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            bonus_likes INTEGER DEFAULT 0,
            referred_by INTEGER
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def db_query(query, params=(), fetchone=False, fetchall=False, commit=False):
    conn = sqlite3.connect('bot_data.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute(query, params)
    res = None
    if fetchone:
        res = cursor.fetchone()
    elif fetchall:
        res = cursor.fetchall()
    if commit:
        conn.commit()
    conn.close()
    return res

def is_owner(user):
    return user.id == OWNER_ID or (user.username and user.username.lower() == OWNER_USERNAME.lower())

def is_subscribed(user_id):
    for ch in REQUIRED_CHANNELS:
        try:
            member = bot.get_chat_member(ch, user_id)
            if member.status not in ['creator', 'administrator', 'member']:
                return False
        except Exception:
            return False
    return True

def get_short_link():
    try:
        url = f"https://gplinks.in/api?api={GPLINKS_API_KEY}&url={TARGET_URL}"
        res = requests.get(url, timeout=10).json()
        if res.get("status") == "success":
            return res.get("shortlink")
        elif "shortenedUrl" in res:
            return res.get("shortenedUrl")
    except Exception as e:
        logger.error(f"GPLinks Error: {e}")
    return f"https://gplinks.in/api?api={GPLINKS_API_KEY}&url={TARGET_URL}"

app = Flask('')

@app.route('/')
def home():
    return "Bot is Alive & Running 24/7!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def call_api(region, uid):
    url = f"https://freefire-like-and-guest-api-by-star.onrender.com/like?uid={uid}&region={region}"
    try:
        response = requests.get(url, timeout=20)
        if response.status_code == 200:
            return response.json()
        return {"error": "Maximum likes limit reached or API Error"}
    except Exception:
        return {"error": "API Failed. Try again later."}

def main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("⭐ FREE LIKES", "💎 BUY VIP / PREMIUM")
    markup.add("🎁 REFER & EARN")
    return markup

def region_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("IND 🇮🇳", "BR 🇧🇷", "US 🇺🇸", "SG 🇸🇬")
    markup.add("🔙 Main Menu")
    return markup

@bot.message_handler(commands=['stopbot'])
def stop_bot_cmd(message):
    if not is_owner(message.from_user):
        return
    open(BOT_CONTROL_FILE, 'w').close()
    bot.reply_to(message, "🛑 Bot stopped exclusively by Owner @rohit2848!")

@bot.message_handler(commands=['startbot'])
def start_bot_cmd(message):
    if not is_owner(message.from_user):
        return
    if os.path.exists(BOT_CONTROL_FILE):
        os.remove(BOT_CONTROL_FILE)
    bot.reply_to(message, "🟢 Bot started/resumed exclusively by Owner @rohit2848!")

@bot.message_handler(commands=['broadcast'])
def broadcast_cmd(message):
    if not is_owner(message.from_user):
        return
    text = message.text.replace('/broadcast', '').strip()
    if not text:
        bot.reply_to(message, "❌ Message likho broadcast karne ke liye! Example: `/broadcast Hello Users`")
        return
    
    users = db_query("SELECT user_id FROM users", fetchall=True)
    success = 0
    failed = 0
    for u in users:
        try:
            bot.send_message(u[0], text)
            success += 1
            time.sleep(0.1)
        except Exception:
            failed += 1
    bot.reply_to(message, f"📢 Broadcast Completed!\n✅ Sent: {success}\n❌ Failed: {failed}")

@bot.message_handler(func=lambda message: True, content_types=['text', 'photo', 'video', 'document', 'audio', 'sticker'])
def all_messages_handler(message):
    if os.path.exists(BOT_CONTROL_FILE):
        if is_owner(message.from_user):
            if message.text in ['/startbot', '/stopbot']:
                pass
            else:
                bot.reply_to(message, "⚠️ Bot abhi OFF hai! Chalu karne ke liye `/startbot` bhejein.")
        return

    user_id = message.from_user.id
    text = message.text

    if text and text.startswith('/start'):
        args = text.split()
        user_data = db_query("SELECT user_id FROM users WHERE user_id = ?", (user_id,), fetchone=True)
        if not user_data:
            referrer_id = None
            if len(args) > 1 and args[1].isdigit():
                possible_ref = int(args[1])
                if possible_ref != user_id:
                    referrer_id = possible_ref
            
            db_query("INSERT INTO users (user_id, bonus_likes, referred_by) VALUES (?, 0, ?)", (user_id, referrer_id), commit=True)
            
            if referrer_id:
                db_query("UPDATE users SET bonus_likes = bonus_likes + 1 WHERE user_id = ?", (referrer_id,), commit=True)
                try:
                    bot.send_message(referrer_id, "🎉 Congratulations! Kisi ne aapke referral link se bot join kiya hai. Aapko +1 Extra Like Bonus mila hai!")
                except Exception:
                    pass

        if not is_subscribed(user_id):
            bot.reply_to(message, "❌ Pehle humara channel @hacklinkpc join karein!")
            return

        welcome_text = (
            "✨ Welcome to VIP Like Services, Leader!\n\n"
            "🎒 I'm Free Fire Instant Likes Bot!\n"
            "⚡ Fast, Safe & 24/7 Active Bot.\n\n"
            "👇 Tap an option below to get started!"
        )
        bot.send_message(message.chat.id, welcome_text, reply_markup=main_menu())

    elif text == "💎 BUY VIP / PREMIUM":
        if not is_subscribed(user_id):
            bot.reply_to(message, "❌ Access Denied! Pehle @hacklinkpc channel join karein.")
            return

        text_msg = (
            "💎 VIP & PREMIUM PLANS\n\n"
            "✨ Benefits:\n"
            "• Unlimited Daily Likes\n"
            "• Instant API Processing\n"
            "• Priority Support\n\n"
            "💸 Pricing:\n"
            "• 1 Day VIP: ₹20\n"
            "• 7 Days VIP: ₹100\n"
            "• Monthly VIP: ₹300\n\n"
            f"📱 UPI ID: {UPI_ID}\n\n"
            "💳 How to Pay:\n"
            "1. Scan the QR code above or copy the UPI ID.\n"
            "2. Make payment and take a screenshot.\n"
            "3. Click below to send proof along with your User ID."
        )
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📩 Send Proof to Owner", url=f"https://t.me/{OWNER_USERNAME}"))
        try:
            bot.send_photo(message.chat.id, photo=QR_CODE_URL, caption=text_msg, reply_markup=markup)
        except Exception as e:
            logger.error(f"Photo error: {e}")
            bot.send_message(message.chat.id, text_msg, reply_markup=markup)

    elif text == "🎁 REFER & EARN":
        if not is_subscribed(user_id):
            bot.reply_to(message, "❌ Access Denied! Pehle @hacklinkpc channel join karein.")
            return

        user_info = db_query("SELECT bonus_likes FROM users WHERE user_id = ?", (user_id,), fetchone=True)
        bonus_likes = user_info[0] if user_info else 0

        bot_info = bot.get_me()
        referral_link = f"https://t.me/{bot_info.username}?start={user_id}"
        text_msg = (
            "🎁 REFERRAL SYSTEM\n\n"
            f"⭐ Aapke Paas Extra Bonus Likes Hain: {bonus_likes}\n\n"
            "Apne doston ko bot share karein! Jab bhi koi dost aapke link se join karega, aapko 1 Extra Like pane ka chance milega!\n\n"
            f"🔗 Aapka Referral Link:\n{referral_link}"
        )
        bot.send_message(message.chat.id, text_msg)

    elif text == "⭐ FREE LIKES":
        if not is_subscribed(user_id):
            bot.reply_to(message, "❌ Access Denied! Pehle @hacklinkpc channel join karein.")
            return

        short_link = get_short_link()
        text_msg = (
            "🔓 UNLOCK FREE LIKES\n\n"
            "Free Likes paane ke liye neeche दिए गए link ko open karke verify karein:\n\n"
            f"🔗 Link: {short_link}\n\n"
            "Complete karne ke baad niche Region choose karein!"
        )
        bot.send_message(message.chat.id, text_msg, reply_markup=region_menu())

    elif text in ["IND 🇮🇳", "BR 🇧🇷", "US 🇺🇸", "SG 🇸🇬"]:
        if not is_subscribed(user_id):
            bot.reply_to(message, "❌ Access Denied! Pehle @hacklinkpc channel join karein.")
            return

        region = text.split()[0]
        msg = bot.send_message(message.chat.id, f"🎯 Selected Region: {region}\n\n📝 Enter your Free Fire UID:")
        bot.register_next_step_handler(msg, process_user_uid, region)

    elif text == "🔙 Main Menu":
        bot.send_message(message.chat.id, "🔙 Main Menu:", reply_markup=main_menu())

def process_user_uid(message, region):
    if os.path.exists(BOT_CONTROL_FILE):
        return
    uid = message.text.strip()
    if not uid.isdigit():
        bot.send_message(message.chat.id, "❌ Invalid UID! Please enter a valid numerical UID.")
        return
    bot.send_message(message.chat.id, "⏳ Processing your request... Please wait.")
    threading.Thread(target=process_like, args=(message, region, uid)).start()

def process_like(message, region, uid):
    response = call_api(region, uid)
    if "error" in response or response.get("status") != "success":
        bot.reply_to(message, f"❌ Request Failed: {response.get('error', 'Unknown Error')}")
        return
    bot.reply_to(message, f"🎉 Likes Sent Successfully to UID: {uid}!")

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    bot.infinity_polling(skip_pending=True)
        
