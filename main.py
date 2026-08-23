import threading
import time
import os
import sqlite3
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import logging
import requests
from flask import Flask

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BOT_TOKEN = "8868364202:AAHT-nhI3bYNv9gHXADiMPBj5V8AgdjnX8U"
REQUIRED_CHANNELS = ["@hacklinkpc"]
OWNER_ID = 7125817223
OWNER_USERNAME = "rohit2848"
UPI_ID = "7605900368@fam"

GPLINKS_API_KEY = "B127680908b90e463b9216880b34fb36e0a6a9c6"
TARGET_URL = "https://t.me/hacklinkpc"
QR_CODE_URL = "https://i.ibb.co/6Js976z/qr-sample.jpg"

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
    fallback_link = f"https://gplinks.in/api?api={GPLINKS_API_KEY}&url={TARGET_URL}"
    try:
        url = f"https://gplinks.in/api?api={GPLINKS_API_KEY}&url={TARGET_URL}"
        res = requests.get(url, timeout=10).json()
        if res.get("status") == "success" and res.get("shortlink"):
            return res.get("shortlink")
        elif "shortenedUrl" in res and res.get("shortenedUrl"):
            return res.get("shortenedUrl")
    except Exception as e:
        logger.error(f"GPLinks Error: {e}")
    return fallback_link

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

def region_inline_menu():
    markup = InlineKeyboardMarkup()
    markup.add(
        InlineKeyboardButton("IND 🇮🇳", callback_data="region_IND"),
        InlineKeyboardButton("BR 🇧🇷", callback_data="region_BR")
    )
    markup.add(
        InlineKeyboardButton("US 🇺🇸", callback_data="region_US"),
        InlineKeyboardButton("SG 🇸🇬", callback_data="region_SG")
    )
    return markup

@bot.callback_query_handler(func=lambda call: call.data == 'claim_verify' or call.data.startswith('region_'))
def callback_handler(call):
    user_id = call.from_user.id
    if os.path.exists(BOT_CONTROL_FILE):
        bot.answer_callback_query(call.id, "⚠️ Bot is currently OFF by Owner @rohit2848.", show_alert=True)
        return

    if call.data == 'claim_verify':
        bot.answer_callback_query(call.id, "✅ Verified Successfully!")
        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="🎯 **Verification Done!**\n\nAb neeche se apna **Free Fire Region** choose karein:",
                reply_markup=region_inline_menu(),
                parse_mode="Markdown"
            )
        except Exception:
            bot.send_message(
                call.message.chat.id,
                "🎯 **Verification Done!**\n\nAb neeche se apna **Free Fire Region** choose karein:",
                reply_markup=region_inline_menu(),
                parse_mode="Markdown"
            )

    elif call.data.startswith('region_'):
        region = call.data.split('_')[1]
        bot.answer_callback_query(call.id)
        msg = bot.send_message(call.message.chat.id, f"🎯 Selected Region: **{region}**\n\n📝 Enter your Free Fire UID:", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_user_uid, region)

@bot.message_handler(func=lambda message: True, content_types=['text', 'photo', 'video', 'document', 'audio', 'sticker'])
def all_messages_handler(message):
    user_id = message.from_user.id
    text = message.text

    user_data = db_query("SELECT user_id FROM users WHERE user_id = ?", (user_id,), fetchone=True)
    if not user_data:
        db_query("INSERT INTO users (user_id, bonus_likes, referred_by) VALUES (?, 0, NULL)", (user_id,), commit=True)

    if os.path.exists(BOT_CONTROL_FILE):
        if is_owner(message.from_user):
            if message.text in ['/startbot', '/stopbot']:
                pass
            else:
                bot.reply_to(message, "⚠️ Bot abhi OFF hai! Chalu karne ke liye `/startbot` bhejein.")
        else:
            bot.reply_to(message, "⚠️ Bot is currently OFF / Under Maintenance by Owner @rohit2848.")
        return

    if text and text.startswith('/start'):
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
            f"📱 UPI ID: `{UPI_ID}`\n\n"
            "💳 How to Pay:\n"
            "1. Scan the QR code or click Pay via UPI.\n"
            "2. Make payment and take a screenshot.\n"
            "3. Send proof to owner along with your User ID."
        )
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("⚡ Pay via UPI (GPay/PhonePe)", url=f"upi://pay?pa={UPI_ID}&pn=VIP%20Likes&cu=INR"))
        markup.add(InlineKeyboardButton("📩 Send Proof to Owner", url=f"https://t.me/{OWNER_USERNAME}"))
        
        try:
            bot.send_photo(message.chat.id, photo=QR_CODE_URL, caption=text_msg, reply_markup=markup, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Photo send error: {e}")
            bot.send_message(message.chat.id, text_msg, reply_markup=markup, parse_mode="Markdown")

    elif text == "⭐ FREE LIKES":
        if not is_subscribed(user_id):
            bot.reply_to(message, "❌ Access Denied! Pehle @hacklinkpc channel join karein.")
            return

        short_link = get_short_link()
        text_msg = (
            "🔓 **UNLOCK FREE LIKES**\n\n"
            "1. Niche **`🔗 Open & Complete Link`** par click karke task complete karein.\n"
            "2. Task complete karke wapas yahan aayein aur **`✅ Complete & Claim Likes`** par click karein!"
        )
        
        inline_kb = InlineKeyboardMarkup()
        inline_kb.add(InlineKeyboardButton("🔗 Open & Complete Link", url=short_link))
        inline_kb.add(InlineKeyboardButton("✅ Complete & Claim Likes", callback_data="claim_verify"))

        bot.send_message(message.chat.id, text_msg, reply_markup=inline_kb, parse_mode="Markdown")

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
    bot.infinity_polling(skip_pending=True, timeout=20, long_polling_timeout=10)
               
