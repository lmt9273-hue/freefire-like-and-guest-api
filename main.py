import threading
import time
import os
from datetime import datetime, timedelta
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import logging
import requests
from flask import Flask

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BOT_TOKEN = "8868364202:AAFZt2y9zXgSGat93gMIO4xZa99G4eZP3uc"
REQUIRED_CHANNELS = ["@hacklinkpc"]
OWNER_ID = 7125817223
OWNER_USERNAME = "rohit2848"
UPI_ID = "7605900368@fam"

# Raw GitHub URL for QR Code Image
QR_CODE_URL = "https://raw.githubusercontent.com/lmt9273-hue/freefire-like-and-guest-api/refs/heads/main/photo_2026-08-23_10-14-11.jpg"

bot = telebot.TeleBot(BOT_TOKEN)
like_tracker = {}
user_database = set()

def is_subscribed(user_id):
    for ch in REQUIRED_CHANNELS:
        try:
            member = bot.get_chat_member(ch, user_id)
            if member.status not in ['creator', 'administrator', 'member']:
                return False
        except Exception:
            return False
    return True

# Flask Server for Render
app = Flask('')

@app.route('/')
def home():
    return "Bot is Alive & Running 24/7!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def reset_limits():
    while True:
        now_utc = datetime.utcnow()
        next_reset = (now_utc + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
        sleep_seconds = (next_reset - now_utc).total_seconds()
        time.sleep(sleep_seconds)
        like_tracker.clear()
        logger.info("Limits reset executed.")

threading.Thread(target=reset_limits, daemon=True).start()

def call_api(region, uid):
    url = f"https://freefire-like-and-guest-api-by-star.onrender.com/like?uid={uid}&region={region}"
    try:
        response = requests.get(url, timeout=20)
        if response.status_code == 200:
            return response.json()
        return {"error": "Maximum likes limit reached or API Error"}
    except Exception:
        return {"error": "API Failed. Try again later."}

def get_user_limit(user_id):
    return 999999999 if user_id == OWNER_ID else 30

def main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("⭐ FREE LIKES", "💎 BUY VIP / PREMIUM")
    return markup

def region_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("IND 🇮🇳", "BR 🇧🇷", "US 🇺🇸", "SG 🇸🇬")
    return markup

@bot.message_handler(commands=['start'])
def start_command(message):
    if not is_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ Pehle humara channel @hacklinkpc join karein!")
        return

    user_database.add(message.from_user.id)
    welcome_text = (
        "✨ **Welcome to VIP Like Services, Leader!**\n\n"
        "🎒 **I'm Free Fire Instant Likes Bot!**\n"
        "⚡ Fast, Safe & 24/7 Active Bot.\n"
        "👇 Tap an option below to get started!"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=main_menu())

@bot.message_handler(func=lambda message: message.text == "💎 BUY VIP / PREMIUM")
def buy_vip_click(message):
    if not is_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ Access Denied! Pehle @hacklinkpc channel join karein.")
        return

    text = (
        "💎 **VIP & PREMIUM PLANS**\n\n"
        "✨ **Benefits:**\n"
        "• Unlimited Daily Likes\n"
        "• Instant API Processing\n"
        "• Priority Support\n\n"
        "💸 **Pricing:**\n"
        "• 1 Day VIP: ₹20\n"
        "• 7 Days VIP: ₹100\n"
        "• Monthly VIP: ₹300\n\n"
        f"📱 **UPI ID:** `{UPI_ID}`\n\n"
        "💳 **How to Pay:**\n"
        "1. Scan the QR code above or copy the UPI ID.\n"
        "2. Make payment and take a screenshot.\n"
        "3. Click below to send proof along with your User ID."
    )
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("📩 Send Proof to Owner", url=f"https://t.me/{OWNER_USERNAME}"))
    try:
        bot.send_photo(message.chat.id, photo=QR_CODE_URL, caption=text, reply_markup=markup, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Photo error: {e}")
        bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "⭐ FREE LIKES")
def free_likes_click(message):
    if not is_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ Access Denied! Pehle @hacklinkpc channel join karein.")
        return

    bot.send_message(message.chat.id, "⭐ **FREE LIKES MENU**\nSelect your region:", reply_markup=region_menu())

@bot.message_handler(func=lambda message: message.text in ["IND 🇮🇳", "BR 🇧🇷", "US 🇺🇸", "SG 🇸🇬"])
def ask_uid(message):
    if not is_subscribed(message.from_user.id):
        bot.reply_to(message, "❌ Access Denied! Pehle @hacklinkpc channel join karein.")
        return

    region = message.text.split()[0]
    msg = bot.send_message(message.chat.id, f"🎯 **Selected Region:** `{region}`\n\n📝 Enter your Free Fire **UID**:")
    bot.register_next_step_handler(msg, process_user_uid, region)

def process_user_uid(message, region):
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
    bot.reply_to(message, f"🎉 Likes Sent Successfully to UID: `{uid}`!")

@bot.message_handler(func=lambda message: message.text == "🔙 Main Menu")
def back_menu(message):
    bot.send_message(message.chat.id, "🔙 Main Menu:", reply_markup=main_menu())

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    bot.infinity_polling(skip_pending=True)
                       
