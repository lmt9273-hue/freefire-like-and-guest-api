import os
import threading
import logging
import urllib.parse
import secrets
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

# Updated with your active Shrinkme API Key
SHRINKME_API_KEY = "79bb11f8fbdbfc1371908a293b010548208e1f24"

bot = telebot.TeleBot(BOT_TOKEN)

# Dynamic Verification Tokens {token: user_id}
valid_tokens = {}

def is_owner(user):
    if user.id == ALLOWED_USER_ID:
        return True
    if user.username and user.username.lower() in ALLOWED_USERNAMES:
        return True
    return False

def check_force_join(user_id):
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
    """Shrinkme.io API Link Generator"""
    api_url = f"https://shrinkme.io/api?api={SHRINKME_API_KEY}&url={urllib.parse.quote(target_url)}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    try:
        response = requests.get(api_url, headers=headers, timeout=12)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "success" and "shortenedUrl" in data:
                return data["shortenedUrl"]
            elif "shortenedUrl" in data:
                return data["shortenedUrl"]
    except Exception as e:
        logger.error(f"Shrinkme Fetch Failure: {e}")
    return None

def get_qr_url(amount):
    upi_string = f"upi://pay?pa={UPI_ID}&pn=Amlan%20malik&am={amount}&cu=INR"
    return f"https://api.qrserver.com/v1/create-qr-code/?size=350x350&data={urllib.parse.quote(upi_string)}"

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

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    global is_bot_stopped
    user_id = call.from_user.id
    
    if is_bot_stopped and not is_owner(call.from_user):
        bot.answer_callback_query(call.id, "🛠️ Bot is under maintenance!", show_alert=True)
        return

    if call.data == 'check_join_again':
        if check_force_join(user_id):
            bot.answer_callback_query(call.id, "✅ Verified!")
            bot.send_message(call.message.chat.id, "🎉 Access Granted!", reply_markup=main_menu())
        else:
            bot.answer_callback_query(call.id, "❌ Channel join nahi hai!", show_alert=True)
        return

    if not is_owner(call.from_user) and not check_force_join(user_id):
        bot.answer_callback_query(call.id, "❌ Access Denied!", show_alert=True)
        bot.send_message(
            call.message.chat.id,
            "⚠️ **Access Revoked!** Please join the channel first:",
            reply_markup=force_join_menu(),
            parse_mode="Markdown"
        )
        return

    if call.data.startswith('pkg_'):
        parts = call.data.split('_')
        amount, plan_name = parts[1], parts[2]
        
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
        except Exception:
            bot.send_message(call.message.chat.id, caption, parse_mode="Markdown")

    elif call.data.startswith('region_'):
        region = call.data.split('_')[1]
        bot.answer_callback_query(call.id)
        msg = bot.send_message(call.message.chat.id, f"🎯 Selected Region: **{region}**\n\n📝 Enter Free Fire UID:", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_user_uid, region)

@bot.message_handler(func=lambda message: True)
def all_messages_handler(message):
    global is_bot_stopped
    text = message.text
    user_id = message.from_user.id

    if is_owner(message.from_user):
        if text == "/stopbot":
            is_bot_stopped = True
            bot.reply_to(message, "🛑 **Bot Stopped!**")
            return
        elif text == "/startbot":
            is_bot_stopped = False
            bot.reply_to(message, "🟢 **Bot Started!**")
            return

    if is_bot_stopped and not is_owner(message.from_user):
        bot.reply_to(message, "🛠️ **Bot is under maintenance.**")
        return

    if not is_owner(message.from_user) and not check_force_join(user_id):
        bot.send_message(
            message.chat.id,
            "⚠️ **Access Denied!** Join channel first:",
            reply_markup=force_join_menu(),
            parse_mode="Markdown"
        )
        return

    if text and text.startswith('/start'):
        args = text.split()
        
        # Checking dynamic claim verification token
        if len(args) > 1 and args[1].startswith('claim_'):
            token = args[1]
            if token in valid_tokens and valid_tokens[token] == user_id:
                del valid_tokens[token]
                bot.send_message(
                    message.chat.id,
                    "🎉 **Task Verified Successfully!**\n\nAb apna **Free Fire Region** choose karein:",
                    reply_markup=region_inline_menu(),
                    parse_mode="Markdown"
                )
            else:
                bot.send_message(message.chat.id, "❌ **Expired ya Invalid Link!** Please naya link generate karein.")
            return

        bot.send_message(message.chat.id, "✨ Welcome to Free Fire VIP Likes Bot!", reply_markup=main_menu())

    elif text == "🎁 REFER & EARN":
        ref_text = f"🎁 **REFER & EARN**\n\n🔗 Link:\n`https://t.me/{BOT_USERNAME}?start={user_id}`"
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
        token = f"claim_{secrets.token_hex(4)}"
        valid_tokens[token] = user_id
        
        target_destination = f"https://t.me/{BOT_USERNAME}?start={token}"
        short_link = get_short_link(target_destination)
        
        if not short_link:
            bot.send_message(message.chat.id, "⚠️ Server busy! Press **⭐ FREE LIKES** again in 5 seconds.")
            return

        text_msg = (
            "🔓 **FREE LIKES TASK**\n\n"
            "1️⃣ Neeche diye gaya **`🔗 Open & Complete Link`** par click karein.\n"
            "2️⃣ Steps complete karke **Get Link** button dabayein.\n"
            "3️⃣ Direct Telegram open karke **START** par click karein, verification ho jayega!"
        )
        
        inline_kb = InlineKeyboardMarkup()
        inline_kb.add(InlineKeyboardButton("🔗 Open & Complete Link", url=short_link))

        bot.send_message(message.chat.id, text_msg, reply_markup=inline_kb, parse_mode="Markdown")

def process_user_uid(message, region):
    uid = message.text.strip()
    if not uid.isdigit():
        bot.send_message(message.chat.id, "❌ Invalid UID! Numbers only.")
        return
    bot.send_message(message.chat.id, f"🎉 Request Queued for UID: {uid} ({region})!")

if __name__ == "__main__":
    threading.Thread(target=run_web, daemon=True).start()
    bot.infinity_polling(skip_pending=True, timeout=20, long_polling_timeout=10)
            
