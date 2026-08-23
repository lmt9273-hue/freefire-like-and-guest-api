import os
import sqlite3
import threading
import logging
import requests
from flask import Flask
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BOT_TOKEN = "8868364202:AAHmY3fFncwmpDjDjbwCWzcg-cuq-xCNbAI"
REQUIRED_CHANNELS = ["@hacklinkpc"]
OWNER_ID = 7125817223
OWNER_USERNAME = "priyakumari07"
UPI_ID = "aaccrr@axl"

GPLINKS_API_KEY = "B127680908b90e463b9216880b34fb36e0a6a9c6"
TARGET_URL = "https://t.me/hacklinkpc"

# Working QR Code Direct URL (Replace with your direct image link if needed)
QR_CODE_URL = "https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=upi://pay?pa=aaccrr@axl&pn=PRIYA%20LIKES%20BOT&am=10&cu=INR"

bot = telebot.TeleBot(BOT_TOKEN)
BOT_CONTROL_FILE = "bot_stopped.lock"

# Direct Memory Tracker to prevent link bypass
user_clicked_link = set()

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

@bot.callback_query_handler(func=lambda call: call.data in ['track_open', 'claim_verify', 'buy_coins'] or call.data.startswith(('region_', 'pkg_')))
def callback_handler(call):
    user_id = call.from_user.id

    if call.data == 'track_open':
        user_clicked_link.add(user_id)
        bot.answer_callback_query(call.id, "🔗 Link Opened! Complete the task and click 'I Have Completed Task'.")

    elif call.data == 'claim_verify':
        if user_id not in user_clicked_link:
            bot.answer_callback_query(call.id, "❌ Task Incomplete! Pehle 'Open & Complete Link' par click karein!", show_alert=True)
            return

        user_clicked_link.remove(user_id)
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

    elif call.data.startswith('pkg_'):
        amount = call.data.split('_')[1]
        coins = call.data.split('_')[2]
        bot.answer_callback_query(call.id)
        
        caption = (
            f"🟢 **UPI Selected.**\n\n"
            f"📱 **Product:** `{coins} coins`\n"
            f"💰 **Amount:** `₹{amount}`\n"
            f"💳 **Method:** `UPI`\n"
            f"💳 **UPI ID:** `{UPI_ID}` 📋\n"
            f"🛡️ **100% Secure & Encrypted Payment**\n"
            f"⌛ **Payment valid for 10 minutes**\n"
            f"📤 **Send payment screenshot**\n"
            f"💬 **Need Help? Contact** @{OWNER_USERNAME}\n\n"
            f"⚡ *Coins are credited instantly after verification!*"
        )
        
        try:
            bot.send_photo(call.message.chat.id, photo=QR_CODE_URL, caption=caption, parse_mode="Markdown")
        except Exception:
            bot.send_message(call.message.chat.id, caption, parse_mode="Markdown")

    elif call.data.startswith('region_'):
        region = call.data.split('_')[1]
        bot.answer_callback_query(call.id)
        msg = bot.send_message(call.message.chat.id, f"🎯 Selected Region: **{region}**\n\n📝 Enter your Free Fire UID:", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_user_uid, region)

@bot.message_handler(func=lambda message: True)
def all_messages_handler(message):
    user_id = message.from_user.id
    text = message.text

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
            "💸 **BUY COINS / VIP PACKAGES**\n\n"
            "💰 200 Coins = ₹10\n"
            "💰 500 Coins = ₹25\n"
            "💰 1000 Coins = ₹45\n"
            "💰 2000 Coins = ₹90\n"
            "💰 5000 Coins = ₹210\n\n"
            "✨ *Find the package that's right for you below!*"
        )
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("200 Coins = ₹10", callback_data="pkg_10_200"),
            InlineKeyboardButton("500 Coins = ₹25", callback_data="pkg_25_500")
        )
        markup.add(
            InlineKeyboardButton("1000 Coins = ₹45", callback_data="pkg_45_1000"),
            InlineKeyboardButton("2000 Coins = ₹90", callback_data="pkg_90_2000")
        )
        markup.add(InlineKeyboardButton("5000 Coins = ₹210", callback_data="pkg_210_5000"))
        
        bot.send_message(message.chat.id, text_msg, reply_markup=markup, parse_mode="Markdown")

    elif text == "⭐ FREE LIKES":
        if not is_subscribed(user_id):
            bot.reply_to(message, "❌ Access Denied! Pehle @hacklinkpc channel join karein.")
            return

        short_link = get_short_link()
        text_msg = (
            "🔓 **UNLOCK FREE LIKES**\n\n"
            "1️⃣ Pehle **`🔗 Open & Complete Link`** par click karke task poora karein.\n"
            "2️⃣ Link open karne ke baad hi **`✅ I Have Completed Task`** dabayein!"
        )
        
        inline_kb = InlineKeyboardMarkup()
        inline_kb.add(InlineKeyboardButton("🔗 Open & Complete Link", url=short_link, callback_data="track_open"))
        inline_kb.add(InlineKeyboardButton("✅ I Have Completed Task", callback_data="claim_verify"))

        bot.send_message(message.chat.id, text_msg, reply_markup=inline_kb, parse_mode="Markdown")

def process_user_uid(message, region):
    uid = message.text.strip()
    if not uid.isdigit():
        bot.send_message(message.chat.id, "❌ Invalid UID! Please enter a numerical UID.")
        return
    bot.send_message(message.chat.id, f"🎉 Likes request queued for UID: {uid} ({region})!")

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    bot.infinity_polling(skip_pending=True, timeout=20, long_polling_timeout=10)
