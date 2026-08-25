import os
import telebot
import requests
import urllib.parse
from threading import Thread
from flask import Flask
from telebot import types

# --- WEB SERVER FOR RENDER KEEP ALIVE ---
app = Flask('')

@app.route('/')
def home():
    return "Bot status: ONLINE"

def run():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- CONFIGURATION ---
BOT_TOKEN = "8868364202:AAFl-7nyZU4HBoD5OB4ADcM-54sQDe6G7IA"
bot = telebot.TeleBot(BOT_TOKEN)

UPI_NAME = "Amlan Malik"
UPI_ID = "7605900368@fam"
OWNER_USERNAME = "rohit2848"

user_ids = set()
bot_active = True

PLANS = {
    "10": "1 Day VIP",
    "25": "3 Days VIP",
    "45": "7 Days VIP",
    "90": "15 Days VIP",
    "210": "30 Days VIP"
}

def is_owner(user):
    return bool(user.username and user.username.lower() == OWNER_USERNAME.lower())

def register_user(message):
    user_ids.add(message.chat.id)

def get_qr_code_url(amount, plan_name):
    encoded_name = urllib.parse.quote(UPI_NAME)
    encoded_note = urllib.parse.quote(f"Plan: {plan_name}")
    upi_payload = f"upi://pay?pa={UPI_ID}&pn={encoded_name}&am={amount}&cu=INR&tn={encoded_note}"
    return f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={urllib.parse.quote(upi_payload)}"

# --- DYNAMIC UID DATA GENERATOR ---
def calculate_dynamic_user_data(uid):
    digits = "".join(filter(str.isdigit, str(uid)))
    seed = int(digits) if digits else 123456
    
    before = (seed % 7800) + 1200
    given = 100
    after = before + given
    player_num = (seed % 899) + 100
    
    return {
        "name": f"Player_{player_num}",
        "before": before,
        "given": given,
        "after": after
    }

def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_free = types.KeyboardButton("⭐ FREE LIKES")
    btn_vip = types.KeyboardButton("💎 BUY VIP / PREMIUM")
    btn_refer = types.KeyboardButton("🎁 REFER & EARN")
    markup.add(btn_free, btn_vip)
    markup.add(btn_refer)
    return markup

# --- START COMMAND ---
@bot.message_handler(commands=['start'])
def start_command(message):
    try:
        register_user(message)
        if not bot_active and not is_owner(message.from_user):
            bot.reply_to(message, "🛑 Bot currently offline by Owner!")
            return

        welcome_text = (
            "👑 Welcome to Free VIP Likes Bot!\n\n"
            "How to use:\n"
            "Send command: /like ind [UID]\n"
            "Example: /like ind 3030839920\n\n"
            "🚀 Status: Live Engine Active"
        )
        bot.send_message(message.chat.id, welcome_text, reply_markup=get_main_keyboard())
    except Exception as e:
        print(f"Error in start: {e}")

# --- LIKE COMMAND HANDLER (ROBUST WITHOUT PARSE MODE CRASH) ---
@bot.message_handler(commands=['like'])
def handle_like_command(message):
    try:
        register_user(message)
        if not bot_active and not is_owner(message.from_user):
            bot.reply_to(message, "🛑 Bot is Locked by Owner!")
            return

        args = message.text.split()
        if len(args) < 3:
            bot.reply_to(message, "⚠️ Format: /like ind [UID]\nExample: /like ind 3030839920")
            return

        region = args[1].upper()
        target_uid = args[2]

        res = calculate_dynamic_user_data(target_uid)

        report = (
            f"⚡ FF AUTOLIKE ⚡\n"
            f"💎 VIP SENT SUCCESSFULLY\n"
            f"(API 1)\n\n"
            f"👤 NAME: {res['name']}\n"
            f"🆔 UID: {target_uid}\n"
            f"🌍 REGION: {region}\n"
            f"📊 BEFORE: {res['before']}\n"
            f"🎁 GIVEN: {res['given']}\n"
            f"👑 AFTER: {res['after']}\n\n"
            f"🏷️ OWNER: @{OWNER_USERNAME}"
        )

        markup = types.InlineKeyboardMarkup(row_width=2)
        btn1 = types.InlineKeyboardButton(f"⚡ {res['given']} LIKES", callback_data="none")
        btn2 = types.InlineKeyboardButton("👤 OWNER ↗️", url=f"https://t.me/{OWNER_USERNAME}")
        markup.add(btn1, btn2)

        bot.send_message(message.chat.id, report, reply_markup=markup)
    except Exception as e:
        print(f"Error in like: {e}")
        bot.reply_to(message, "❌ Request Process karne me error aaya. Dynamic server retrying...")

# --- BUY VIP HANDLER ---
@bot.message_handler(func=lambda message: message.text == "💎 BUY VIP / PREMIUM")
def handle_buy_vip(message):
    try:
        register_user(message)
        vip_text = (
            "💎 BUY VIP / PREMIUM PACKAGES\n\n"
            "⚡ 1 Day VIP = ₹10\n"
            "⚡ 3 Days VIP = ₹25\n"
            "⚡ 7 Days VIP = ₹45\n"
            "⚡ 15 Days VIP = ₹90\n"
            "⚡ 30 Days VIP = ₹210\n\n"
            "👇 Select plan to generate QR Code:"
        )
        
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("₹10 (1 Day)", callback_data="pay_10"),
            types.InlineKeyboardButton("₹25 (3 Days)", callback_data="pay_25"),
            types.InlineKeyboardButton("₹45 (7 Days)", callback_data="pay_45"),
            types.InlineKeyboardButton("₹90 (15 Days)", callback_data="pay_90"),
            types.InlineKeyboardButton("₹210 (30 Days)", callback_data="pay_210")
        )
        bot.send_message(message.chat.id, vip_text, reply_markup=markup)
    except Exception as e:
        print(f"Error in buy vip: {e}")

# --- CALLBACK QUERY HANDLER ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_"))
def handle_qr_callback(call):
    try:
        amount = call.data.split("_")[1]
        plan_name = PLANS.get(amount, "VIP Plan")
        qr_url = get_qr_code_url(amount, plan_name)

        caption_text = (
            "💳 UPI Payment Details\n\n"
            f"👤 Name: {UPI_NAME}\n"
            f"📌 Plan: {plan_name}\n"
            f"💰 Amount: ₹{amount}\n"
            f"🆔 UPI ID: {UPI_ID}\n\n"
            f"📲 Send Screenshot to: @{OWNER_USERNAME}"
        )

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("⚠️ CONTACT OWNER", url=f"https://t.me/{OWNER_USERNAME}"))

        bot.send_photo(call.message.chat.id, photo=qr_url, caption=caption_text, reply_markup=markup)
    except Exception as e:
        print(f"Error in qr callback: {e}")

# --- BUTTON HANDLERS ---
@bot.message_handler(func=lambda message: message.text == "⭐ FREE LIKES")
def handle_free_likes(message):
    bot.reply_to(message, "🎁 Free Likes Command:\n/like ind [YOUR_UID]")

@bot.message_handler(func=lambda message: message.text == "🎁 REFER & EARN")
def handle_refer(message):
    bot.reply_to(message, f"🔗 Your Referral Link:\nhttps://t.me/FreeFirebrazilFF_BOT?start={message.from_user.id}")

# --- CATCH ALL OTHER MESSAGES ---
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    if message.text.startswith('/like'):
        handle_like_command(message)

if __name__ == "__main__":
    keep_alive()
    print("Bot Started Successfully...")
    bot.infinity_polling(timeout=20, long_polling_timeout=10)
    
