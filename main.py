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
BOT_USERNAME = "FreeFirebrazilFF_BOT"

REQUIRED_CHANNELS = ["@hacklinkpc"]

ALLOWED_USER_ID = 7125817223  
ALLOWED_USERNAMES = ["rohit2848", "rohitx_2848"]

is_bot_stopped = False

UPI_ID = "7605900368@fam"
ACCOUNT_NAME = "Amlan malik"

# Updated API Key from your video
GPLINKS_API_KEY = "b480bd48837b6b20f20db558add38fc763270af"
TARGET_URL = f"https://t.me/{BOT_USERNAME}?start=claim"

bot = telebot.TeleBot(BOT_TOKEN)

def is_owner(user):
    if user.id == ALLOWED_USER_ID:
        return True
    if user.username and user.username.lower() in ALLOWED_USERNAMES:
        return True
    return False

def check_force_join(user_id):
    """Real-time check: verifies if user is STILL in the channel"""
    for ch in REQUIRED_CHANNELS:
        try:
            member = bot.get_chat_member(ch, user_id)
            if member.status in ['left', 'kicked']:
                return False
        except Exception as e:
            logger.error(f"Error checking channel join: {e}")
            return False
    return True

def force_join_menu():
    markup = InlineKeyboardMarkup()
    for ch in REQUIRED_CHANNELS:
        ch_clean = ch.replace("@", "")
        markup.add(InlineKeyboardButton(f"📢 Join Channel ({ch})", url=f"https://t.me/{ch_clean}"))
    markup.add(InlineKeyboardButton("🔄 Verify Join Status", callback_data="check_join_again"))
    return markup

def get_short_link(target_url):
    """Fetches the actual shortened URL from GPLinks API"""
    try:
        api_url = f"https://gplinks.in/api?api={GPLINKS_API_KEY}&url={urllib.parse.quote(target_url)}"
        response = requests.get(api_url, timeout=10)
        data = response.json()
        if data.get("status") == "success" and "shortenedUrl" in data:
            return data["shortenedUrl"]
    except Exception as e:
        logger.error(f"GPLinks API Error: {e}")
    return target_url

def get_qr_url(amount):
    upi_string = f"upi://pay?pa={UPI_ID}&pn=Amlan%20malik&am={amount}&cu=INR"
    return f"https://api.qrserver.com/v1/create-qr-code/?size=350x350&data={urllib.parse.quote(upi_string)}"

user_clicked_link = set()

app = Flask('')

@app.route('/')
def home():
    return "Bot status running!"

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
    global is_bot_stopped
    user_id = call.from_user.id
    
    if is_bot_stopped and not is_owner(call.from_user):
        bot.answer_callback_query(call.id, "🛠️ Bot is under maintenance!", show_alert=True)
        return

    # Verify Button Action
    if call.data == 'check_join_again':
        if check_force_join(user_id):
            bot.answer_callback_query(call.id, "✅ Verified! Welcome back.")
            bot.send_message(call.message.chat.id, "🎉 Access Granted! Options select karein:", reply_markup=main_menu())
        else:
            bot.answer_callback_query(call.id, "❌ Channel join nahi hai! Pehle join karein.", show_alert=True)
        return

    # Real-time Channel Leave Check
    if not is_owner(call.from_user) and not check_force_join(user_id):
        bot.answer_callback_query(call.id, "❌ Access Denied! Aapne channel leave kar diya hai.", show_alert=True)
        bot.send_message(
            call.message.chat.id,
            "⚠️ **Access Revoked!**\n\nAapne humara official channel leave kar diya hai. Bot use karne ke liye dubara join karein:",
            reply_markup=force_join_menu(),
            parse_mode="Markdown"
        )
        return

    if call.data == 'track_open':
        user_clicked_link.add(user_id)
        bot.answer_callback_query(call.id, "🔗 Link opened! Task poora karke 'I Have Completed Task' dabayein.")

    elif call.data == 'claim_verify':
        if user_id not in user_clicked_link:
            bot.answer_callback_query(call.id, "❌ Task Incomplete! Pehle link open karein!", show_alert=True)
            return

        user_clicked_link.remove(user_id)
        bot.answer_callback_query(call.id, "✅ Task Verified!")
        
        bot.send_message(
            call.message.chat.id,
            "🎯 **Task Verified!**\n\nAb apna **Free Fire Region** choose karein:",
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
            f"📤 Screenshot bhejein: @rohit2848"
        )
        
        try:
            bot.send_photo(call.message.chat.id, photo=qr_image_url, caption=caption, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Error sending photo: {e}")
            bot.send_message(call.message.chat.id, caption, parse_mode="Markdown")

    elif call.data.startswith('region_'):
        region = call.data.split('_')[1]
        bot.answer_callback_query(call.id)
        msg = bot.send_message(call.message.chat.id, f"🎯 Selected Region: **{region}**\n\n📝 Enter Free Fire UID:", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_user_uid, region)

# --- MESSAGE HANDLER ---
@bot.message_handler(func=lambda message: True)
def all_messages_handler(message):
    global is_bot_stopped
    text = message.text
    user_id = message.from_user.id

    if is_owner(message.from_user):
        if text == "/stopbot":
            is_bot_stopped = True
            bot.reply_to(message, "🛑 **Bot Stopped Silently!**")
            return
        elif text == "/startbot":
            is_bot_stopped = False
            bot.reply_to(message, "🟢 **Bot Started Silently!**")
            return

    if is_bot_stopped and not is_owner(message.from_user):
        bot.reply_to(message, "🛠️ **Bot is under maintenance.**")
        return

    # Real-time Check for commands / buttons
    if not is_owner(message.from_user) and not check_force_join(user_id):
        bot.send_message(
            message.chat.id,
            "⚠️ **Access Denied!**\n\nAapne channel leave kar diya hai. Access paane ke liye dubara join karein:",
            reply_markup=force_join_menu(),
            parse_mode="Markdown"
        )
        return

    if text and text.startswith('/start'):
        welcome_text = "✨ Welcome to Free Fire VIP Likes Bot!\n\n👇 Tap an option below:"
        bot.send_message(message.chat.id, welcome_text, reply_markup=main_menu())

    elif text == "🎁 REFER & EARN":
        unique_referral_link = f"https://t.me/{BOT_USERNAME}?start={user_id}"
        ref_text = f"🎁 **REFER & EARN**\n\n🔗 Your Invite Link:\n`{unique_referral_link}`"
        bot.send_message(message.chat.id, ref_text, parse_mode="Markdown")

    elif text == "💎 BUY VIP / PREMIUM":
        text_msg = "💎 **BUY VIP PACKAGES**\n\nSelect a package below:"
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
        short_link = get_short_link(TARGET_URL)
        text_msg = "🔓 Complete task to get Free Likes:"
        
        inline_kb = InlineKeyboardMarkup()
        inline_kb.add(InlineKeyboardButton("🔗 Open & Complete Link", url=short_link, callback_data="track_open"))
        inline_kb.add(InlineKeyboardButton("✅ I Have Completed Task", callback_data="claim_verify"))

        bot.send_message(message.chat.id, text_msg, reply_markup=inline_kb, parse_mode="Markdown")

def process_user_uid(message, region):
    if not is_owner(message.from_user) and not check_force_join(message.from_user.id):
        bot.send_message(message.chat.id, "⚠️ Access Denied! Please rejoin the channel first.", reply_markup=force_join_menu())
        return

    uid = message.text.strip()
    if not uid.isdigit():
        bot.send_message(message.chat.id, "❌ Invalid UID! Please enter numbers only.")
        return
    bot.send_message(message.chat.id, f"🎉 Request Queued for UID: {uid} ({region})!")

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    bot.infinity_polling(skip_pending=True, timeout=20, long_polling_timeout=10)
        
