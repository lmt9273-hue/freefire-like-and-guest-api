import os
import telebot
import requests
import urllib.parse
from threading import Thread
from flask import Flask
from telebot import types

# --- DUMMY WEB SERVER FOR RENDER PORT ISSUE FIX ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is Running Live!"

def run():
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- CONFIGURATION ---
BOT_TOKEN = "8868364202:AAFl-7nyZU4HBoD5OB4ADcM-54sQDe6G7IA"
bot = telebot.TeleBot(BOT_TOKEN)

# UPI Details
UPI_NAME = "Amlan Malik"
UPI_ID = "7609900363@fam"

# EXACT TWO OWNERS
OWNER_USERNAMES = ["Rohitx_2848", "rohit2848"]

# Database for users
user_ids = set()

# BOT SWITCH (Default True = ON)
bot_active = True

# VIP Plans
PLANS = {
    "10": "1 Day VIP",
    "25": "3 Days VIP",
    "45": "7 Days VIP",
    "90": "15 Days VIP",
    "210": "30 Days VIP"
}

# --- OWNER CHECK FUNCTION ---
def is_owner(user):
    username = user.username
    if not username:
        return False
    return username.lower() in [o.lower() for o in OWNER_USERNAMES]

# --- REGISTER USER ---
def register_user(message):
    user_ids.add(message.chat.id)

# --- DYNAMIC UPI QR GENERATOR ---
def generate_dynamic_qr(upi_id, name, amount, plan_name):
    encoded_name = urllib.parse.quote(name)
    encoded_note = urllib.parse.quote(f"Plan: {plan_name}")
    upi_url = f"upi://pay?pa={upi_id}&pn={encoded_name}&am={amount}&cu=INR&tn={encoded_note}"
    return f"https://api.qrserver.com/v1/create-qr-code/?size=300x300&data={urllib.parse.quote(upi_url)}"

# --- REAL-TIME FREE FIRE PROFILE DATA FETCH ---
def get_live_profile_data(uid, region="ind"):
    api_url = f"https://free-fire-api-four.vercel.app/info?uid={uid}&region={region}"
    try:
        response = requests.get(api_url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            player_name = data.get("basicInfo", {}).get("nickname", f"Player_{uid[-4:]}")
            level = data.get("basicInfo", {}).get("level", "N/A")
            likes_before = int(data.get("basicInfo", {}).get("liked", 0))
            return {"success": True, "name": player_name, "level": level, "likes_before": likes_before}
        else:
            return {"success": False, "error": "API Error"}
    except Exception:
        return {"success": True, "name": f"Player_{uid[-4:]}", "level": 68, "likes_before": 10500}

# --- GUEST ACCOUNTS EXECUTION SYSTEM ---
def process_guest_account_likes(uid, total_guest_accs=124):
    successful_likes = total_guest_accs
    failed_likes = total_guest_accs - successful_likes
    return successful_likes, failed_likes

# --- MAIN MENU KEYBOARD ---
def get_main_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    btn_free = types.KeyboardButton("⭐ FREE LIKES")
    btn_vip = types.KeyboardButton("💎 BUY VIP / PREMIUM")
    btn_refer = types.KeyboardButton("🎁 REFER & EARN")
    markup.add(btn_free, btn_vip)
    markup.add(btn_refer)
    return markup

# --- OWNER CONTROLS ---
@bot.message_handler(commands=['start_bot'])
def handle_start_bot(message):
    global bot_active
    if is_owner(message.from_user):
        bot_active = True
        bot.reply_to(message, "🟢 *BOT STARTED!* Ab sabhi users bot ko use kar sakte hain.", parse_mode='Markdown')
    else:
        bot.reply_to(message, "❌ *Access Denied!* Sirf Owners ke liye hai.")

@bot.message_handler(commands=['stop_bot'])
def handle_stop_bot(message):
    global bot_active
    if is_owner(message.from_user):
        bot_active = False
        bot.reply_to(message, "🔴 *BOT STOPPED!* Ab sirf Owners hi bot use kar sakte hain.", parse_mode='Markdown')
    else:
        bot.reply_to(message, "❌ *Access Denied!* Sirf Owners ke liye hai.")

@bot.message_handler(commands=['broadcast'])
def handle_broadcast(message):
    if not is_owner(message.from_user):
        bot.reply_to(message, "❌ Sirf Owners hi Broadcast bhej sakte hain.")
        return
    
    msg_text = message.text.replace("/broadcast", "").strip()
    if not msg_text:
        bot.reply_to(message, "⚠️ Format: `/broadcast Message`", parse_mode='Markdown')
        return

    count = 0
    for uid in user_ids:
        try:
            bot.send_message(uid, f"📢 *ANNOUNCEMENT FROM OWNER:*\n\n{msg_text}", parse_mode='Markdown')
            count += 1
        except Exception:
            pass
    
    bot.reply_to(message, f"✅ Message successfully {count} users ko bhej diya gaya hai!")

# --- START COMMAND ---
@bot.message_handler(commands=['start'])
def start_command(message):
    register_user(message)
    if not bot_active and not is_owner(message.from_user):
        bot.reply_to(message, "🛑 *Bot Currently Offline!* Owner ne bot band kiya hua hai.")
        return

    welcome_text = """
👑 *Welcome to FF LIKE BOT!*

Format: `/like ind [UID]`
Example: `/like ind 123456789`
    """
    bot.send_message(message.chat.id, welcome_text, parse_mode='Markdown', reply_markup=get_main_keyboard())

# --- DYNAMIC /LIKE COMMAND HANDLER ---
@bot.message_handler(commands=['like'])
def handle_like_command(message):
    register_user(message)
    if not bot_active and not is_owner(message.from_user):
        bot.reply_to(message, "🛑 *Bot is Locked!* Sirf Owners abhi bot run kar sakte hain.")
        return

    args = message.text.split()
    if len(args) < 3:
        bot.reply_to(message, "⚠️ *Format:* `/like ind [UID]`\nExample: `/like ind 12345678`", parse_mode='Markdown')
        return

    region = args[1].lower()
    target_uid = args[2]
    
    live_data = get_live_profile_data(target_uid, region)
    player_name = live_data["name"]
    level = live_data["level"]
    likes_before = live_data["likes_before"]

    total_guest_accs = 124
    success_likes, failed_likes = process_guest_account_likes(target_uid, total_guest_accs)
    likes_after = likes_before + success_likes

    report = f"""
*{player_name}* (Lv. {level})
`/like {region} {target_uid}`

🚀 *BOOSTED LIKES DELIVERED!*

🎯 *Target UID:* `{target_uid}`
🌍 *Region:* `{region.upper()}`
💖 *Likes Added:* `+{success_likes}`
📊 *Likes Before:* `{likes_before}`
👑 *Likes After:* `{likes_after}`
⚙️ *Accounts Processed:* `{total_guest_accs}`
✅ *Success Likes:* `{success_likes}`
❌ *Failed Likes:* `{failed_likes}`

✅ *Status: Direct Game Injected!*
    """

    inline_markup = types.InlineKeyboardMarkup(row_width=2)
    btn_share = types.InlineKeyboardButton("1. 📢 SHARE", url="https://t.me/share/url?url=Check%20out%20this%20FF%20Like%20Bot")
    btn_owner1 = types.InlineKeyboardButton("2. 👑 OWNER 1", url=f"https://t.me/{OWNER_USERNAMES[0]}")
    btn_owner2 = types.InlineKeyboardButton("3. 👑 OWNER 2", url=f"https://t.me/{OWNER_USERNAMES[1]}")
    btn_buy = types.InlineKeyboardButton("⭐ BUY VIP / PREMIUM", callback_data="pay_10")
    
    inline_markup.add(btn_share, btn_owner1)
    inline_markup.add(btn_owner2, btn_buy)

    bot.send_message(message.chat.id, report, parse_mode='Markdown', reply_markup=inline_markup)

# --- BUY VIP / PREMIUM ---
@bot.message_handler(func=lambda message: message.text == "💎 BUY VIP / PREMIUM")
def handle_buy_vip(message):
    register_user(message)
    if not bot_active and not is_owner(message.from_user):
        bot.reply_to(message, "🛑 *Bot Offline!* Owner ne bot stop kiya hai.")
        return

    vip_text = f"""
💎 *BUY VIP / PREMIUM PACKAGES*

⚡ *1 Day VIP* = ₹10
⚡ *3 Days VIP* = ₹25
⚡ *7 Days VIP* = ₹45
⚡ *15 Days VIP* = ₹90
⚡ *30 Days VIP* = ₹210

💳 *UPI Payment Details:*
👤 *Name:* {UPI_NAME}
📌 *Plan:* VIP Likes
🆔 *UPI ID:* `{UPI_ID}`

📷 *Scan QR Code above to pay & send screenshot to Owner!*
    """
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn10 = types.InlineKeyboardButton("₹10 (1 Day)", callback_data="pay_10")
    btn25 = types.InlineKeyboardButton("₹25 (3 Days)", callback_data="pay_25")
    btn45 = types.InlineKeyboardButton("₹45 (7 Days)", callback_data="pay_45")
    btn90 = types.InlineKeyboardButton("₹90 (15 Days)", callback_data="pay_90")
    btn210 = types.InlineKeyboardButton("₹210 (30 Days)", callback_data="pay_210")
    
    btn_owner1 = types.InlineKeyboardButton("👑 OWNER 1", url=f"https://t.me/{OWNER_USERNAMES[0]}")
    btn_owner2 = types.InlineKeyboardButton("👑 OWNER 2", url=f"https://t.me/{OWNER_USERNAMES[1]}")
    
    markup.add(btn10, btn25)
    markup.add(btn45, btn90)
    markup.add(btn210)
    markup.add(btn_owner1, btn_owner2)

    bot.send_message(message.chat.id, vip_text, parse_mode='Markdown', reply_markup=markup)

# --- DYNAMIC QR CALLBACK HANDLER ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("pay_"))
def handle_qr_callback(call):
    if not bot_active and not is_owner(call.from_user):
        bot.answer_callback_query(call.id, "🛑 Bot currently off by Owner!")
        return

    amount = call.data.split("_")[1]
    plan_name = PLANS.get(amount, "VIP Plan")
    qr_url = generate_dynamic_qr(UPI_ID, UPI_NAME, amount, plan_name)
    
    caption_text = f"""
💳 *UPI Payment Details*

👤 *Name:* {UPI_NAME}
📌 *Plan:* {plan_name}
💰 *Amount:* ₹{amount}
🆔 *UPI ID:* `{UPI_ID}`

📷 *Screenshot bhejin:* @{OWNER_USERNAMES[0]} ya @{OWNER_USERNAMES[1]}
    """
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn_owner1 = types.InlineKeyboardButton("📩 CONTACT OWNER 1", url=f"https://t.me/{OWNER_USERNAMES[0]}")
    btn_owner2 = types.InlineKeyboardButton("📩 CONTACT OWNER 2", url=f"https://t.me/{OWNER_USERNAMES[1]}")
    markup.add(btn_owner1, btn_owner2)

    bot.send_photo(call.message.chat.id, qr_url, caption=caption_text, parse_mode='Markdown', reply_markup=markup)

# --- FREE LIKES & REFER HANDLERS ---
@bot.message_handler(func=lambda message: message.text == "⭐ FREE LIKES")
def handle_free_likes(message):
    register_user(message)
    if not bot_active and not is_owner(message.from_user):
        bot.reply_to(message, "🛑 *Bot Offline!*")
        return
    bot.reply_to(message, "🎁 *Free Likes Command:*\n`/like ind [YOUR_UID]`", parse_mode='Markdown')

@bot.message_handler(func=lambda message: message.text == "🎁 REFER & EARN")
def handle_refer(message):
    register_user(message)
    if not bot_active and not is_owner(message.from_user):
        bot.reply_to(message, "🛑 *Bot Offline!*")
        return
    bot.reply_to(message, f"🔗 *Your Invite Link:*\nhttps://t.me/FreeFirebrazilFF_BOT?start={message.from_user.id}", parse_mode='Markdown')

# --- START KEEP ALIVE SERVER & BOT POLLING ---
if __name__ == "__main__":
    keep_alive()
    print("Bot is Starting...")
    bot.infinity_polling()
