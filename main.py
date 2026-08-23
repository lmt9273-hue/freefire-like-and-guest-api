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

# ALLOWED ADMIN DETAILS (Aapki ID aur Username)
ALLOWED_USER_ID = 7125817223  
ALLOWED_USERNAME = "rohitx_2848"  # Small letters mein verification ke liye

DEV_MODE = True  # True = Sirf aap chala payenge

UPI_ID = "7605900368@fam"
ACCOUNT_NAME = "Amlan malik"

GPLINKS_API_KEY = "B127680908b90e463b9216880b34fb36e0a6a9c6"
BOT_USERNAME = "FreeFireIzzapiFF_BOT"
TARGET_URL = f"https://t.me/{BOT_USERNAME}?start=claim"

bot = telebot.TeleBot(BOT_TOKEN)

def is_authorized(user):
    """User ID ya Username mein se koi ek bhi match hoga toh bot access mil jayega."""
    if not DEV_MODE:
        return True
    
    # User ID Check
    if user.id == ALLOWED_USER_ID:
        return True
        
    # Username Check
    if user.username and user.username.lower() == ALLOWED_USERNAME:
        return True
        
    return False

def get_qr_url(amount):
    upi_string = f"upi://pay?pa={UPI_ID}&pn=Amlan%20malik&am={amount}&cu=INR"
    return f"https://api.qrserver.com/v1/create-qr-code/?size=350x350&data={urllib.parse.quote(upi_string)}"

user_clicked_link = set()

app = Flask('')

@app.route('/')
def home():
    return "Bot is Running!"

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

# --- CALLBACK QUERY HANDLER ---
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if not is_authorized(call.from_user):
        bot.answer_callback_query(call.id, "⚠️ Bot is under maintenance for public users!", show_alert=True)
        return

    user_id = call.from_user.id

    if call.data == 'track_open':
        user_clicked_link.add(user_id)
        bot.answer_callback_query(call.id, "🔗 Link opened! Task poora karke 'I Have Completed Task' dabayein.")

    elif call.data == 'claim_verify':
        if user_id not in user_clicked_link:
            bot.answer_callback_query(call.id, "❌ Task Incomplete! Pehle 'Open & Complete Link' par click karein!", show_alert=True)
            return

        user_clicked_link.remove(user_id)
        bot.answer_callback_query(call.id, "✅ Verified Successfully!")
        
        bot.send_message(
            call.message.chat.id,
            "🎯 **Task Verified Successfully!**\n\nAb neeche se apna **Free Fire Region** choose karein:",
            reply_markup=region_inline_menu(),
            parse_mode="Markdown"
        )

    elif call.data.startswith('pkg_'):
        parts = call.data.split('_')
        amount = parts[1]
        plan_name = parts[2]
        
        bot.answer_callback_query(call.id)
        qr_image_url = get_qr_url(amount)
        
        caption = (
            f"🟢 **UPI Payment Details**\n\n"
            f"👤 **Name:** `{ACCOUNT_NAME}`\n"
            f"📦 **Plan:** `{plan_name} VIP`\n"
            f"💰 **Amount:** `₹{amount}`\n"
            f"💳 **UPI ID:** `{UPI_ID}`\n\n"
            f"📥 **Scan QR Code or Pay directly on UPI ID.**\n"
            f"📤 **Send payment screenshot to:** @{ALLOWED_USERNAME}\n\n"
            f"⚡ *VIP activates instantly after verification!*"
        )
        
        try:
            bot.send_photo(call.message.chat.id, photo=qr_image_url, caption=caption, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Error sending photo: {e}")
            bot.send_message(call.message.chat.id, caption, parse_mode="Markdown")

    elif call.data.startswith('region_'):
        region = call.data.split('_')[1]
        bot.answer_callback_query(call.id)
        msg = bot.send_message(call.message.chat.id, f"🎯 Selected Region: **{region}**\n\n📝 Enter your Free Fire UID:", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_user_uid, region)

# --- MESSAGE HANDLER ---
@bot.message_handler(func=lambda message: True)
def all_messages_handler(message):
    if not is_authorized(message.from_user):
        bot.reply_to(message, "🛠️ **Bot is under maintenance.**\nAccess restricted by owner.")
        return

    text = message.text
    user_id = message.from_user.id

    if text and text.startswith('/start'):
        welcome_text = (
            "✨ Welcome to Free Fire VIP Likes Bot!\n\n"
            "⚡ Fast, Safe & 24/7 Active Bot.\n\n"
            "👇 Tap an option below to get started!"
        )
        bot.send_message(message.chat.id, welcome_text, reply_markup=main_menu())

    elif text == "🎁 REFER & EARN":
        referral_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
        ref_text = (
            "🎁 **REFER & EARN SYSTEM**\n\n"
            "📢 Share your referral link with friends!\n"
            "🚀 Earn Free VIP Likes for every referral.\n\n"
            f"🔗 **Your Invite Link:**\n`{referral_link}`"
        )
        bot.send_message(message.chat.id, ref_text, parse_mode="Markdown")

    elif text == "💎 BUY VIP / PREMIUM":
        text_msg = (
            "💎 **BUY VIP / PREMIUM PACKAGES**\n\n"
            "💵 1 Day VIP = ₹10\n"
            "💵 3 Days VIP = ₹25\n"
            "💵 7 Days VIP = ₹45\n"
            "💵 15 Days VIP = ₹90\n"
            "💵 30 Days VIP = ₹210\n\n"
            "✨ *Select a Package Below to Get QR Code!*"
        )
        markup = InlineKeyboardMarkup()
        markup.add(
            InlineKeyboardButton("₹10 (1 Day)", callback_data="pkg_10_1Day"),
            InlineKeyboardButton("₹25 (3 Days)", callback_data="pkg_25_3Days")
        )
        markup.add(
            InlineKeyboardButton("₹45 (7 Days)", callback_data="pkg_45_7Days"),
            InlineKeyboardButton("₹90 (15 Days)", callback_data="pkg_90_15Days")
        )
        markup.add(InlineKeyboardButton("₹210 (30 Days)", callback_data="pkg_210_30Days"))
        
        bot.send_message(message.chat.id, text_msg, reply_markup=markup, parse_mode="Markdown")

    elif text == "⭐ FREE LIKES":
        short_link = f"https://gplinks.in/api?api={GPLINKS_API_KEY}&url={urllib.parse.quote(TARGET_URL)}"
        text_msg = (
            "🔓 **UNLOCK FREE LIKES**\n\n"
            "1️⃣ Pehle **`🔗 Open & Complete Link`** par click karke task poora karein.\n"
            "2️⃣ Task complete karne ke baad **`✅ I Have Completed Task`** dabayein!"
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
    
