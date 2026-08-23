import os
import telebot
import requests
import time
import threading
from datetime import datetime, timedelta
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# === CONFIG ===
BOT_TOKEN = "8868364202:AAEVRd3NQYm-vxj73TUGuY7MA1a4krmo0yk"

if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN not found!")
    sys.exit(1)

REQUIRED_CHANNELS = ["@hacklinkpc"]
OWNER_ID = 7128817223
OWNER_USERNAME = "@rohit2848"
UPI_ID = "7605900368@fam"  

# Direct Image Link for FamPay QR
QR_CODE_URL = "https://i.postimg.cc/mD8TdtZz/61380.jpg"

bot = telebot.TeleBot(BOT_TOKEN)
like_tracker = {}   
user_database = set()  

# === DATA RESET ===
def reset_limits():
    while True:
        try:
            now_utc = datetime.utcnow()
            next_reset = (now_utc + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
            sleep_seconds = (next_reset - now_utc).total_seconds()
            time.sleep(sleep_seconds)
            like_tracker.clear()
            logger.info("✅ Daily limits reset at 00:00 UTC.")
        except Exception as e:
            logger.error(f"Error in reset thread: {e}")

threading.Thread(target=reset_limits, daemon=True).start()

def call_api(region, uid):
    url = f"https://freefire-like-and-guest-api-br9t.onrender.com/like?sg={region}&uid={uid}"
    try:
        response = requests.get(url, timeout=20)
        if response.status_code != 200:
            return {"⚠️Invalid": " Maximum likes reached for today."}
        return response.json()
    except Exception:
        return {"error": "API Failed. Try again later."}

def get_user_limit(user_id):
    if user_id == OWNER_ID:
        return 999999999  
    return 1  

# === KEYBOARDS ===
def main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        KeyboardButton("⭐ FREE LIKES"),
        KeyboardButton("💎 BUY VIP / PREMIUM"),
        KeyboardButton("📊 MY PROFILE"),
        KeyboardButton("👥 REFER & EARN"),
        KeyboardButton("👑 OWNER"),
        KeyboardButton("🆘 HELP")
    )
    return markup

def region_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    markup.add(
        KeyboardButton("IND 🇮🇳"), KeyboardButton("BR 🇧🇷"), KeyboardButton("US 🇺🇸"),
        KeyboardButton("SG 🇸🇬"), KeyboardButton("RU 🇷🇺"), KeyboardButton("ID 🇮🇩"),
        KeyboardButton("🔙 Back")
    )
    return markup

# === COMMANDS & HANDLERS ===
@bot.message_handler(commands=['start'])
def start_command(message):
    user_id = message.from_user.id
    user_database.add(user_id)
    
    welcome_text = (
        "✨ **Welcome to VIP Like Services, Leader!**\n\n"
        "🎒 **I'm Free Fire Instant Likes Bot!**\n"
        "⚡ Fast, Safe & 24/7 Active Bot.\n"
        "👇 Tap an option below to get started!"
    )
    bot.send_message(message.chat.id, welcome_text, reply_markup=main_menu(), parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "📊 MY PROFILE")
def profile_click(message):
    user_id = message.from_user.id
    usage = like_tracker.get(user_id, {"used": 0})
    limit = get_user_limit(user_id)
    limit_str = "Unlimited 👑" if limit > 1000 else str(limit)
    
    profile_text = (
        f"👤 **YOUR PROFILE STATS**\n\n"
        f"🆔 **User ID:** `{user_id}`\n"
        f"📊 **Daily Requests Used:** `{usage.get('used', 0)} / {limit_str}`\n"
        f"⚡ **Plan Status:** {'VIP Owner' if user_id == OWNER_ID else 'Free Tier'}\n\n"
        f"💡 *Upgrade to VIP to get Unlimited Daily Likes!*"
    )
    bot.send_message(message.chat.id, profile_text, parse_mode="Markdown")

# === PAYMENT / VIP SYSTEM ===
@bot.message_handler(func=lambda message: message.text == "💎 BUY VIP / PREMIUM")
def buy_vip_click(message):
    text = (
        "💎 **VIP & PREMIUM PLANS**\n\n"
        "🚀 **Benefits:**\n"
        "• Unlimited Daily Likes\n"
        "• Instant API Processing\n"
        "• Priority Support\n\n"
        "💳 **Pricing:**\n"
        "• 1 Day VIP: ₹20\n"
        "• 7 Days VIP: ₹100\n"
        "• Monthly VIP: ₹300\n\n"
        f"📌 **UPI ID:** `{UPI_ID}`\n\n"
        "📸 **How to Pay:**\n"
        "1. Scan the QR code above or copy the UPI ID.\n"
        "2. Make payment and take a screenshot.\n"
        "3. Click below to send proof along with your User ID to Owner!"
    )
    markup = InlineKeyboardMarkup()
    btn = InlineKeyboardButton("📩 Send Proof to Owner", url=f"https://t.me/{OWNER_USERNAME.strip('@')}")
    markup.add(btn)
    
    try:
        # Direct URL photo send
        bot.send_photo(message.chat.id, photo=QR_CODE_URL, caption=text, reply_markup=markup, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Image Error: {e}")
        bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "⭐ FREE LIKES")
def free_likes_click(message):
    text = "💖 **FREE LIKES SECTION**\n\n🚀 Select your region to claim free likes!"
    bot.send_message(message.chat.id, text, reply_markup=region_menu(), parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text in ["IND 🇮🇳", "BR 🇧🇷", "US 🇺🇸", "SG 🇸🇬", "RU 🇷🇺", "ID 🇮🇩"])
def ask_uid(message):
    region = message.text.split()[0]
    text = f"🌐 **Region:** {region}\n🎯 **Enter your Free Fire UID below:**"
    msg = bot.send_message(message.chat.id, text, parse_mode="Markdown")
    bot.register_next_step_handler(msg, process_user_uid, region)

def process_user_uid(message, region):
    uid = message.text.strip()
    if not uid.isdigit():
        bot.send_message(message.chat.id, "❌ Invalid UID! Numbers only.", reply_markup=main_menu())
        return

    bot.send_message(message.chat.id, f"🔄 **Processing Request...**\n🆔 UID: {uid}\n🌐 Region: {region}")
    threading.Thread(target=process_like, args=(message, region, uid)).start()

def process_like(message, region, uid):
    user_id = message.from_user.id
    now_utc = datetime.utcnow()
    usage = like_tracker.get(user_id, {"used": 0, "last_used": now_utc - timedelta(days=1)})

    if now_utc.date() > usage["last_used"].date():
        usage["used"] = 0

    max_limit = get_user_limit(user_id)
    if usage["used"] >= max_limit:
        bot.reply_to(message, "⚠️ You have exceeded your daily limit! Upgrade to VIP for unlimited requests.")
        return

    processing_msg = bot.reply_to(message, "⏳ Sending likes... Please wait...")
    response = call_api(region, uid)

    if "error" in response:
        bot.edit_message_text(chat_id=processing_msg.chat.id, message_id=processing_msg.message_id, text=f"⚠️ API Error: {response['error']}")
        return

    if not isinstance(response, dict) or response.get("status") != 1:
        bot.edit_message_text(chat_id=processing_msg.chat.id, message_id=processing_msg.message_id, text="❌ Limit reached for this UID today! Try again after 24 hrs.")
        return

    try:
        player_name = response.get("PlayerNickname", "N/A")
        likes_given = str(response.get("LikesGivenByAPI", "N/A"))
        likes_after = str(response.get("LikesafterCommand", "N/A"))

        usage["used"] += 1
        usage["last_used"] = now_utc
        like_tracker[user_id] = usage

        res_text = (
            f"✅ *Request Successful!*\n\n"
            f"👤 *Name:* `{player_name}`\n"
            f"🆔 *UID:* `{uid}`\n"
            f"📈 *Likes Added:* `{likes_given}`\n"
            f"🗿 *Total Likes:* `{likes_after}`\n"
        )
        bot.edit_message_text(chat_id=processing_msg.chat.id, message_id=processing_msg.message_id, text=res_text, parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, "⚠️ Something went wrong processing the request.")

@bot.message_handler(func=lambda message: message.text == "🔙 Back")
def back_menu(message):
    bot.send_message(message.chat.id, "🔙 Main Menu", reply_markup=main_menu())

@bot.message_handler(func=lambda message: message.text == "👥 REFER & EARN")
def refer_click(message):
    bot_username = bot.get_me().username
    ref_link = f"https://t.me/{bot_username}?start={message.from_user.id}"
    bot.send_message(message.chat.id, f"👥 **REFERRAL LINK:**\n\n`{ref_link}`\n\nShare this link to earn VIP rewards!", parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "👑 OWNER")
def owner_click(message):
    bot.send_message(message.chat.id, f"👑 **BOT OWNER:** {OWNER_USERNAME}\n🆔 **ID:** `{OWNER_ID}`", parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "🆘 HELP")
def help_click(message):
    bot.send_message(message.chat.id, "📖 Use **⭐ FREE LIKES** button to get instant likes, or buy VIP for unlimited access!", parse_mode="Markdown")

from flask import Flask
import threading

app = Flask('')

@app.route('/')
def home():
    return "Bot is Alive & Running 24/7!"

def run_web():
    app.run(host='0.0.0.0', port=8080)

if __name__ == "__main__":
    t = threading.Thread(target=run_web)
    t.start()
    
    print("Bot is running in Polling Mode...")
    bot.infinity_polling(skip_pending=True)
    
    
