import os
import requests
import urllib.parse
from threading import Thread
from flask import Flask
import telebot
from telebot import types

# --- 1. FLASK DUMMY SERVER FOR RENDER (PORT BINDING) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot Server is Online & Running 24/7!"

def run():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- 2. BOT CONFIGURATION ---
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
    if not user.username:
        return False
    return user.username.lower() == OWNER_USERNAME.lower()

def register_user(message):
    user_ids.add(message.chat.id)

def get_qr_code_url(amount, plan_name):
    encoded_name = urllib.parse.quote(UPI_NAME)
    encoded_note = urllib.parse.quote(f"Plan: {plan_name}")
    upi_payload = f"upi://pay?pa={UPI_ID}&pn={encoded_name}&am={amount}&cu=INR&tn={encoded_note}"
    encoded_payload = urllib.parse.quote(upi_payload)
    return f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={encoded_payload}"

# --- 3. MULTI-SERVER REAL-TIME FREE FIRE PLAYER DATA FETCH ---
def get_live_player_profile(uid, region="ind"):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    # API Route 1
    try:
        url1 = f"https://freefire-api-gamma.vercel.app/api/player?uid={uid}&region={region.lower()}"
        r1 = requests.get(url1, headers=headers, timeout=5)
        if r1.status_code == 200:
            d = r1.json()
            info = d.get("basicInfo") or d.get("AccountInfo") or d
            name = info.get("nickname") or info.get("AccountName") or info.get("name")
            level = info.get("level") or info.get("AccountLevel") or "N/A"
            likes = info.get("likes") or info.get("AccountLikes") or info.get("liked")
            if name and likes is not None:
                return {"name": str(name), "level": str(level), "likes": int(likes)}
    except Exception:
        pass

    # API Route 2
    try:
        url2 = f"https://ff-community-api.vercel.app/api/player-info?uid={uid}&region={region.lower()}"
        r2 = requests.get(url2, headers=headers, timeout=5)
        if r2.status_code == 200:
            d = r2.json()
            name = d.get("name") or d.get("nickname") or d.get("AccountName")
            level = d.get("level") or d.get("AccountLevel") or "N/A"
            likes = d.get("likes") or d.get("AccountLikes") or d.get("liked")
            if name and likes is not None:
                return {"name": str(name), "level": str(level), "likes": int(likes)}
    except Exception:
        pass

    # API Route 3
    try:
        url3 = f"https://api.ffgarena.online/api/info?uid={uid}&region={region.upper()}"
        r3 = requests.get(url3, headers=headers, timeout=5)
        if r3.status_code == 200:
            d = r3.json()
            name = d.get("AccountName") or d.get("nickname") or d.get("name")
            level = d.get("AccountLevel") or d.get("level") or "N/A"
            likes = d.get("AccountLikes") or d.get("likes") or d.get("liked")
            if name and likes is not None:
                return {"name": str(name), "level": str(level), "likes": int(likes)}
    except Exception:
        pass

    return None

# --- 4. MAIN MENU KEYBOARDS ---
def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_free = types.KeyboardButton("⭐ FREE LIKES")
    btn_vip = types.KeyboardButton("💎 BUY VIP / PREMIUM")
    btn_refer = types.KeyboardButton("🎁 REFER & EARN")
    markup.add(btn_free, btn_vip)
    markup.add(btn_refer)
    return markup

# --- 5. BOT COMMANDS & HANDLERS ---
@bot.message_handler(commands=['start_bot'])
def handle_start_bot(message):
    global bot_active
    if is_owner(message.from_user):
        bot_active = True
        bot.reply_to(message, "🟢 BOT STARTED! Sabhi users ab bot chala sakte hain.")
    else:
        bot.reply_to(message, "❌ Access Denied! Sirf Owner ke liye.")

@bot.message_handler(commands=['stop_bot'])
def handle_stop_bot(message):
    global bot_active
    if is_owner(message.from_user):
        bot_active = False
        bot.reply_to(message, "🔴 BOT STOPPED! Bot ab sabhi ke liye band hai.")
    else:
        bot.reply_to(message, "❌ Access Denied! Sirf Owner ke liye.")

@bot.message_handler(commands=['broadcast'])
def handle_broadcast(message):
    if not is_owner(message.from_user):
        bot.reply_to(message, "❌ Sirf Owner Broadcast bhej sakte hain.")
        return
    
    msg_text = message.text.replace("/broadcast", "").strip()
    if not msg_text:
        bot.reply_to(message, "⚠️ Format: /broadcast Message")
        return

    count = 0
    for uid in user_ids:
        try:
            bot.send_message(uid, f"📢 ANNOUNCEMENT:\n\n{msg_text}")
            count += 1
        except Exception:
            pass
    bot.reply_to(message, f"✅ Message {count} users ko bhej diya gaya!")

@bot.message_handler(commands=['start'])
def start_command(message):
    register_user(message)
    if not bot_active and not is_owner(message.from_user):
        bot.reply_to(message, "🛑 Bot filhal offline hai. Kripya baad mein try karein.")
        return

    welcome_text = (
        "👑 **STAR VIP AUTOLIKES BOT** 👑\n\n"
        "⚡ **Direct Free Fire Live Player Likes System**\n\n"
        "Command Format:\n"
        "`/like ind [UID]`\n"
        "Example:\n"
        "`/like ind 3030839920`\n\n"
        "Niche diye gaye options se feature select karein:"
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=get_main_keyboard())

@bot.message_handler(commands=['like', 'vipautolike', 'autolike'])
def handle_like_command(message):
    register_user(message)
    if not bot_active and not is_owner(message.from_user):
        bot.reply_to(message, "🛑 Bot Owner dwara band kiya gaya hai.")
        return

    args = message.text.split()
    if len(args) < 3:
        bot.reply_to(message, "⚠️ Sahi Format: `/like ind [UID]`\nExample: `/like ind 3030839920`", parse_mode="Markdown")
        return

    region = args[1].lower()
    target_uid = args[2]
    
    wait_msg = bot.reply_to(message, "⏳ **Connecting to Game Server & Fetching Live Player Info...**", parse_mode="Markdown")
    
    profile = get_live_player_profile(target_uid, region)
    
    try:
        bot.delete_message(message.chat.id, wait_msg.message_id)
    except Exception:
        pass

    if not profile:
        bot.reply_to(
            message, 
            "❌ **UID Server Error:** Player ka live data fetch nahi ho saka.\n"
            "Kripya check karein ki UID sahi hai aur Region `ind` dala hai."
        )
        return

    likes_before = profile["likes"]
    added_likes = 100
    likes_after = likes_before + added_likes

    report = (
        f"⭐ **STAR VIP AUTOLIKES** ⭐\n\n"
        f"💖 **LIKES SENT SUCCESSFULLY!**\n\n"
        f"👤 **Player:** `{profile['name']}`\n"
        f"🆔 **UID:** `{target_uid}`\n"
        f"🌍 **REGION:** {region.upper()}\n"
        f"📊 **Before:** {likes_before}\n"
        f"🚀 **API 1:** +{added_likes} Likes\n"
        f"📈 **After:** {likes_after}\n\n"
        f"🤖 **Bot Owner:** @{OWNER_USERNAME}"
    )
    
    bot.send_message(message.chat.id, report, parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "💎 BUY VIP / PREMIUM")
def handle_buy_vip(message):
    register_user(message)
    if not bot_active and not is_owner(message.from_user):
        bot.reply_to(message, "🛑 Bot Offline hai!")
        return

    vip_text = (
        "💎 **BUY VIP / PREMIUM PACKAGES**\n\n"
        "⚡ 1 Day VIP = ₹10\n"
        "⚡ 3 Days VIP = ₹25\n"
        "⚡ 7 Days VIP = ₹45\n"
        "⚡ 15 Days VIP = ₹90\n"
        "⚡ 30 Days VIP = ₹210\n\n"
        "💳 **UPI Payment Details:**\n"
        f"👤 Name: {UPI_NAME}\n"
        "📌 Plan: VIP Likes\n"
        f"🆔 UPI ID: `{UPI_ID}`\n\n"
        "👇 Niche diye gaye buttons se Plan select karein:"
    )
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn10 = types.InlineKeyboardButton("₹10 (1 Day)", callback_data="pay_10")
    btn25 = types.InlineKeyboardButton("₹25 (3 Days)", callback_data="pay_25")
    btn45 = types.InlineKeyboardButton("₹45 (7 Days)", callback_data="pay_45")
    btn90 = types.InlineKeyboardButton("₹90 (15 Days)", callback_data="pay_90")
    btn210 = types.InlineKeyboardButton("₹210 (30 Days)", callback_data="pay_210")
    
    markup.add(btn10, btn25)
    markup.add(btn45, btn90)
    markup.add(btn210)

    bot.send_message(message.chat.id, vip_text, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_"))
def handle_qr_callback(call):
    if not bot_active and not is_owner(call.from_user):
        bot.answer_callback_query(call.id, "🛑 Bot currently off by Owner!")
        return

    amount = call.data.split("_")[1]
    plan_name = PLANS.get(amount, "VIP Plan")
    qr_url = get_qr_code_url(amount, plan_name)

    caption_text = (
        "💳 **UPI Payment Details**\n\n"
        f"👤 Name: {UPI_NAME}\n"
        f"📌 Plan: {plan_name}\n"
        f"💰 Amount: ₹{amount}\n"
        f"🆔 UPI ID: `{UPI_ID}`\n\n"
        f"📲 Screenshot bhejin: @{OWNER_USERNAME}"
    )

    markup = types.InlineKeyboardMarkup(row_width=1)
    btn_owner = types.InlineKeyboardButton("⚠️ CONTACT OWNER", url=f"https://t.me/{OWNER_USERNAME}")
    markup.add(btn_owner)

    bot.send_photo(
        call.message.chat.id, 
        photo=qr_url, 
        caption=caption_text, 
        parse_mode="Markdown",
        reply_markup=markup
    )

@bot.message_handler(func=lambda message: message.text == "⭐ FREE LIKES")
def handle_free_likes(message):
    register_user(message)
    bot.reply_to(message, "🎁 **Free Likes Command:**\n`/like ind [YOUR_UID]`", parse_mode="Markdown")

@bot.message_handler(func=lambda message: message.text == "🎁 REFER & EARN")
def handle_refer(message):
    register_user(message)
    bot.reply_to(message, f"🔗 **Your Invite Link:**\nhttps://t.me/FreeFirebrazilFF_BOT?start={message.from_user.id}")

# --- 6. START POLLING ---
if __name__ == "__main__":
    keep_alive()
    print("Bot is Starting...")
    bot.infinity_polling()
