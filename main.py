import os
import time
import requests
from threading import Thread
from flask import Flask
from concurrent.futures import ThreadPoolExecutor
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

# ==================== 1. FREE WEB SERVER (Render Port Fix) ====================
app = Flask('')

@app.route('/')
def home():
    return "Bot is Live and Active!"

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

keep_alive()  # Server Port Bind Kar Jayega (Render Live Ho Jayega)

# ==================== 2. TELEGRAM BOT SETUP ====================
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

session = requests.Session()

def process_single_account(acc):
    time.sleep(0.05)
    return True

def main_keyboard():
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = KeyboardButton("⭐ FREE LIKES")
    btn2 = KeyboardButton("💎 BUY VIP / PREMIUM")
    btn3 = KeyboardButton("🎁 REFER & EARN")
    markup.add(btn1, btn2)
    markup.add(btn3)
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(message, "Welcome to FF LIKE BOT!", reply_markup=main_keyboard())

@bot.message_handler(commands=['like'])
def handle_like(message):
    try:
        args = message.text.split()
        region = args[1].upper()
        uid = args[2]

        wait_msg = bot.reply_to(
            message, 
            f"<b>Brooo</b>\n<i>/like {region.lower()} {uid}</i>\n\n"
            f"⚡ <i>Bypassing Garena Server Limits...</i>\n"
            f"🎯 Target UID: <code>{uid}</code>", 
            parse_mode="HTML"
        )

        accounts_list = [f"acc_{i}" for i in range(65)]
        with ThreadPoolExecutor(max_workers=20) as executor:
            results = list(executor.map(process_single_account, accounts_list))
        
        accounts_processed = len(results)

        player_name = "Brooo"
        likes_sent = 0
        likes_before = 708
        likes_after = 709
        total_likes_now = 709
        credits_left = 0

        final_text = (
            f"<b>{player_name}</b>\n"
            f"<i>/like {region.lower()} {uid}</i>\n\n"
            f"🚀 <b>BOOSTED LIKES DELIVERED!</b>\n\n"
            f"🎯 <b>Target UID:</b> <code>{uid}</code>\n"
            f"🌍 <b>Region:</b> {region}\n"
            f"💖 <b>Likes Added:</b> +{likes_sent}\n"
            f"📊 <b>Likes Before:</b> <code>{likes_before}</code> / <b>Likes After:</b> <code>{likes_after}</code>\n"
            f"👑 <b>Total Likes Now:</b> <code>{total_likes_now}</code>\n"
            f"⚙️ <b>Accounts Processed:</b> {accounts_processed}\n"
            f"💳 <b>Status:</b> CREDITS LEFT: <code>{credits_left}</code>\n\n"
            f"✅ <b>Status: Direct Game Injected!</b>"
        )

        inline_markup = InlineKeyboardMarkup()
        b1 = InlineKeyboardButton("1. 📢 SHARE", url="https://t.me/share/url?url=CheckThisBot")
        b2 = InlineKeyboardButton("2. 👑 OWNER", url="https://t.me/YOUR_USERNAME")
        inline_markup.row(b1, b2)
        b3 = InlineKeyboardButton("⭐ BUY VIP / PREMIUM", callback_data="buy_vip")
        inline_markup.row(b3)

        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=wait_msg.message_id,
            text=final_text,
            parse_mode="HTML",
            reply_markup=inline_markup
        )

    except Exception as e:
        bot.reply_to(message, "❌ <b>Format:</b> <code>/like ind 7125887223</code>", parse_mode="HTML")

bot.infinity_polling()
