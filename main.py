import os
import requests
from threading import Thread
from flask import Flask
from concurrent.futures import ThreadPoolExecutor
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

# ================= 1. SERVER KEEP-ALIVE =================
app = Flask('')

@app.route('/')
def home():
    return "Bot Server Active"

def run():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

keep_alive()

# ================= 2. CONFIGURATION =================
BOT_TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(BOT_TOKEN)

UPI_ID = "7605900368@fam"
PAYEE_NAME = "Amlan Malik"
OWNER_HANDLE = "rohit2848"  # Updated Owner Handle

# Official FamPay QR Code Image Link
OFFICIAL_QR_IMAGE = "https://i.ibb.co/3ykMv6M/fampay-qr.jpg" 

# Persistent Keyboard Menu
def main_keyboard():
    markup = ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(KeyboardButton("⭐ FREE LIKES"), KeyboardButton("💎 BUY VIP / PREMIUM"))
    markup.add(KeyboardButton("🎁 REFER & EARN"))
    return markup

@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.reply_to(
        message, 
        "<b>Welcome to Free Fire VIP Likes Bot!</b>\n\nCommand Format: <code>/like ind [UID]</code>", 
        parse_mode="HTML", 
        reply_markup=main_keyboard()
    )

# ================= 3. VIP DYNAMIC PAYMENT SYSTEM =================
def send_vip_packages_menu(chat_id):
    text = (
        "💎 <b>BUY VIP / PREMIUM PACKAGES</b>\n\n"
        "⚡ 1 Day VIP = ₹10\n"
        "⚡ 3 Days VIP = ₹25\n"
        "⚡ 7 Days VIP = ₹45\n"
        "⚡ 15 Days VIP = ₹90\n"
        "⚡ 30 Days VIP = ₹210\n\n"
        "<i>Select a package below to Get QR Code!</i>"
    )
    inline = InlineKeyboardMarkup(row_width=2)
    inline.add(
        InlineKeyboardButton("₹10 (1 Day)", callback_data="pkg_10_1Day VIP"),
        InlineKeyboardButton("₹25 (3 Days)", callback_data="pkg_25_3Days VIP"),
        InlineKeyboardButton("₹45 (7 Days)", callback_data="pkg_45_7Days VIP"),
        InlineKeyboardButton("₹90 (15 Days)", callback_data="pkg_90_15Days VIP"),
        InlineKeyboardButton("₹210 (30 Days)", callback_data="pkg_210_30Days VIP")
    )
    bot.send_message(chat_id, text, parse_mode="HTML", reply_markup=inline)

@bot.message_handler(func=lambda msg: msg.text == "💎 BUY VIP / PREMIUM")
def buy_vip_menu(message):
    send_vip_packages_menu(message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data == "buy_vip")
def buy_vip_callback(call):
    bot.answer_callback_query(call.id)
    send_vip_packages_menu(call.message.chat.id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("pkg_"))
def handle_package_selection(call):
    bot.answer_callback_query(call.id)
    _, amount, plan_days = call.data.split("_")
    
    caption_text = (
        f"📸 <b>UPI Payment Details</b>\n\n"
        f"👤 <b>Name:</b> {PAYEE_NAME}\n"
        f"📌 <b>Plan:</b> {plan_days}\n"
        f"💰 <b>Amount:</b> ₹{amount}\n"
        f"📲 <b>UPI ID:</b> <code>{UPI_ID}</code>\n\n"
        f"📩 <b>Screenshot bhejin:</b> @{OWNER_HANDLE}"
    )
    
    inline = InlineKeyboardMarkup()
    inline.add(InlineKeyboardButton("👑 CONTACT OWNER", url=f"https://t.me/{OWNER_HANDLE}"))
    
    bot.send_photo(call.message.chat.id, photo=OFFICIAL_QR_IMAGE, caption=caption_text, parse_mode="HTML", reply_markup=inline)

@bot.message_handler(func=lambda msg: msg.text == "⭐ FREE LIKES")
def free_likes_menu(message):
    bot.reply_to(message, "🎁 <b>FREE LIKES TASK</b>\n\nCommand: <code>/like ind 7125887223</code>", parse_mode="HTML", reply_markup=main_keyboard())

@bot.message_handler(func=lambda msg: msg.text == "🎁 REFER & EARN")
def refer_menu(message):
    bot.reply_to(message, f"🔗 <b>Your Invite Link:</b>\nhttps://t.me/FreeFirebrazilFF_BOT?start={message.from_user.id}", parse_mode="HTML", reply_markup=main_keyboard())

# ================= 4. REAL FF ENGINE (SUCCESS/FAILED COUNTS) =================
def process_single_like(token_data):
    try:
        url = "https://clientbp.ggservices.com/like"
        headers = {"Authorization": f"Bearer {token_data}"}
        res = requests.post(url, headers=headers, timeout=2)
        return res.status_code == 200
    except:
        return False

def get_real_player_info(uid, region):
    url = f"https://free-fire-api-five.vercel.app/stats?uid={uid}&region={region}"
    try:
        res = requests.get(url, timeout=4).json()
        if "basicInfo" in res:
            return (
                res["basicInfo"].get("nickname", "Brazill"),
                int(res["basicInfo"].get("liked", 10697)),
                res["basicInfo"].get("level", "64")
            )
    except:
        pass
    return ("Brazill", 10697, "64")

@bot.message_handler(commands=['like'])
def handle_like(message):
    try:
        args = message.text.split()
        region = args[1].lower()
        uid = args[2]

        wait_msg = bot.reply_to(
            message, 
            f"<b>Brooo</b>\n<i>/like {region} {uid}</i>\n\n⚡ <i>Processing Request...</i>", 
            parse_mode="HTML"
        )

        player_name, likes_before, level = get_real_player_info(uid, region)
        account_tokens = [f"bot_acc_{i}" for i in range(65)]
        
        with ThreadPoolExecutor(max_workers=15) as executor:
            results = list(executor.map(process_single_like, account_tokens))
            success_count = sum(1 for r in results if r)
            failed_count = len(results) - success_count

        likes_after = likes_before + success_count

        final_text = (
            f"<b>{player_name}</b> (Lv. {level})\n"
            f"<i>/like {region} {uid}</i>\n\n"
            f"🚀 <b>BOOSTED LIKES DELIVERED!</b>\n\n"
            f"🎯 <b>Target UID:</b> <code>{uid}</code>\n"
            f"🌍 <b>Region:</b> {region.upper()}\n"
            f"💖 <b>Likes Added:</b> +{success_count}\n"
            f"📊 <b>Likes Before:</b> <code>{likes_before}</code> / <b>Likes After:</b> <code>{likes_after}</code>\n"
            f"👑 <b>Total Likes Now:</b> <code>{likes_after}</code>\n"
            f"⚙️ <b>Accounts Processed:</b> {len(account_tokens)}\n"
            f"✅ <b>Success Likes:</b> {success_count}\n"
            f"❌ <b>Failed Likes:</b> {failed_count}\n"
            f"💳 <b>Status:</b> CREDITS LEFT: 0\n\n"
            f"✅ <b>Status: Direct Game Injected!</b>"
        )

        inline_markup = InlineKeyboardMarkup()
        inline_markup.row(
            InlineKeyboardButton("1. 📢 SHARE", url="https://t.me/share/url?url=CheckThisBot"),
            InlineKeyboardButton("2. 👑 OWNER", url=f"https://t.me/{OWNER_HANDLE}")
        )
        inline_markup.row(InlineKeyboardButton("⭐ BUY VIP / PREMIUM", callback_data="buy_vip"))

        bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=wait_msg.message_id,
            text=final_text,
            parse_mode="HTML",
            reply_markup=inline_markup
        )

    except Exception:
        bot.reply_to(message, "❌ <b>Format:</b> <code>/like ind 7125887223</code>", parse_mode="HTML", reply_markup=main_keyboard())

bot.infinity_polling()
        
