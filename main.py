import os
import sqlite3
import threading
import logging
import urllib.parse
import requests
from flask import Flask
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- CONFIGURATION ---
BOT_TOKEN = "8868364202:AAHmY3fFncwmpDjDjbwCWzcg-cuq-xCNbAI"
REQUIRED_CHANNELS = ["@hacklinkpc"]
OWNER_ID = 7125817223
OWNER_USERNAME = "rohit2848"  # Aapka Telegram Username

# AAPKA EXACT FAMAPP UPI ID
UPI_ID = "7605900368@fam"

GPLINKS_API_KEY = "B127680908b90e463b9216880b34fb36e0a6a9c6"

# BOT REDIRECT URL
BOT_USERNAME = "FreeFireIzzapiFF_BOT"
TARGET_URL = f"https://t.me/{BOT_USERNAME}?start=claim"

bot = telebot.TeleBot(BOT_TOKEN)
BOT_CONTROL_FILE = "bot_stopped.lock"

# Link click tracking
user_clicked_link = set()

def init_db():
    conn = sqlite3.connect('bot_data.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            referred_by INTEGER
        )
    ''')
    conn.commit()
    conn.close()

init_db()

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
    fallback_link = f"https://gplinks.in/api?api={GPLINKS_API_KEY}&url={urllib.parse.quote(TARGET_URL)}"
    try:
        url = f"https://gplinks.in/api?api={GPLINKS_API_KEY}&url={urllib.parse.quote(TARGET_URL)}"
        res = requests.get(url, timeout=10).json()
        if res.get("status") == "success" and res.get("shortlink"):
            return res.get("shortlink")
        elif "shortenedUrl" in res and res.get("shortenedUrl"):
            return res.get("shortenedUrl")
    except Exception as e:
        logger.error(f"GPLinks Error: {e}")
    return fallback_link

def generate_qr_code_url(upi_id, amount, note="VIP Likes"):
    upi_uri = f"upi://pay?pa={upi_id}&pn=Amlan%20Malik&am={amount}&cu=INR&tn={urllib.parse.quote(note)}"
    return f"https://chart.googleapis.com/chart?cht=qr&chs=350x350&chl={urllib.parse.quote(upi_uri)}"

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

@bot.callback_query_handler(func=lambda call: call.data in ['track_open', 'claim_verify'] or call.data.startswith(('region_', 'pkg_')))
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
                text="🎯 **Task Verified Successfully!**\n\nAb neeche se apna **Free Fire Region** choose karein:",
                reply_markup=region_inline_menu(),
                parse_mode="Markdown"
            )
        except Exception:
            bot.send_message(
                call.message.chat.id,
                "🎯 **Task Verified Successfully!**\n\nAb neeche se apna **Free Fire Region** choose karein:",
                reply_markup=region_inline_menu(),
                parse_mode="Markdown"
            )

    elif call.data.startswith('pkg_'):
        amount = call.data.split('_')[1]
        plan_name = call.data.split('_')[2]
        bot.answer_callback_query(call.id)
        
        qr_url = generate_qr_code_url(UPI_ID, amount, f"{plan_name} VIP")
        
        caption = (
            f"🟢 **UPI Selected.**\n\n"
            f"👤 **Name:** `Amlan malik`\n"
            f"📦 **Plan:** `{plan_name} VIP`\n"
            f"💰 **Amount:** `₹{amount}`\n"
            f"💳 **Method:** `UPI / FamApp`\n"
            f"💳 **UPI ID:** `{UPI_ID}` 📋\n\n"
            f"🛡️ **100% Secure Payment**\n"
            f"⌛ **Payment valid for 10 minutes**\n"
            f"📤 **Send payment screenshot to owner**\n"
            f"💬 **Need Help? Contact** @{OWNER_USERNAME}\n\n"
            f"⚡ *VIP Membership activates instantly after verification!*"
        )
        
        try:
            bot.send_photo(call.message.chat.id, photo=qr_url, caption=caption, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Error sending photo: {e}")
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

        if "claim" in text:
            user_clicked_link.add(user_id)

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
            "💎 **BUY VIP / PREMIUM PACKAGES**\n\n"
            "💵 1 Day VIP = ₹10\n"
            "💵 3 Days VIP = ₹25\n"
            "💵 7 Days VIP = ₹45\n"
            "💵 15 Days VIP = ₹90\n"
            "💵 30 Days VIP = ₹210\n\n"
            "✨ *Select a Package Below to View Payment QR!*"
        )
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("₹10 (1 Day VIP)", callback_data="pkg_10_1 Day"),
            InlineKeyboardButton("₹25 (3 Days VIP)", callback_data="pkg_25_3 Days")
        )
        markup.add(
            InlineKeyboardButton("₹45 (7 Days VIP)", callback_data="pkg_45_7 Days"),
            InlineKeyboardButton("₹90 (15 Days VIP)", callback_data="pkg_90_15 Days")
        )
        markup.add(InlineKeyboardButton("₹210 (30 Days VIP)", callback_data="pkg_210_30 Days"))
        
        bot.send_message(message.chat.id, text_msg, reply_markup=markup, parse_mode="Markdown")

    elif text == "⭐ FREE LIKES":
        if not is_subscribed(user_id):
            bot.reply_to(message, "❌ Access Denied! Pehle @hacklinkpc channel join karein.")
            return

        short_link = get_short_link()
        text_msg = (
            "🔓 **UNLOCK FREE LIKES**\n\n"
            "1️⃣ Pehle **`🔗 Open & Complete Link`** par click karke task poora karein.\n"
            "2️⃣ Task complete hone par aap direct bot par aayenge, fir **`✅ I Have Completed Task`** dabayein!"
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
    bot.send_message(message.chat.id, f"🎉 Likes Request Queued for UID: {uid} ({region})!")

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    bot.infinity_polling(skip_pending=True, timeout=20, long_polling_timeout=10)
                         
