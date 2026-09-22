import telebot
import requests

# आपका टेलीग्राम बॉट टोकन
BOT_TOKEN = "8868364202:AAGFIYPodTQ4F5xeYXAwirkqUQVXDjrKPbU"
bot = telebot.TeleBot(BOT_TOKEN)

# फ्लास्क एपीआई सर्वर का पता
API_URL = "http://127.0.0.1:5000/like"

@bot.message_handler(commands=['start'])
def start_msg(message):
    text = (
        "🔥 **फ्री फायर ऑटो-लाइक बॉट तैयार है, लीडर!**\n\n"
        "लाइक भेजने के लिए इस तरह लिखो:\n"
        "`/like <UID>`\n\n"
        "उदाहरण: `/like 123456789`"
    )
    bot.reply_to(message, text, parse_mode="Markdown")

@bot.message_handler(commands=['like'])
def handle_like(message):
    args = message.text.split()
    
    if len(args) < 2:
        bot.reply_to(message, "⚠️ लीडर, यूआईडी तो लिखो!\nउदाहरण: `/like 123456789`", parse_mode="Markdown")
        return

    target_uid = args[1].strip()
    
    if not target_uid.isdigit():
        bot.reply_to(message, "❌ यूआईडी सिर्फ नंबरों में होनी चाहिए!")
        return

    status_msg = bot.reply_to(message, "⏳ लाइक भेजे जा रहे हैं, 10-15 सेकंड रुको...")

    try:
        # लोकल सर्वर पर रिक्वेस्ट भेजना (BD टोकन के साथ)
        params = {
            "uid": target_uid,
            "server_name": "BD"
        }
        response = requests.get(API_URL, params=params, timeout=40)
        
        if response.status_code == 200:
            data = response.json()
            
            player_name = data.get("PlayerNickname", "Unknown")
            before_likes = data.get("LikesbeforeCommand", 0)
            after_likes = data.get("LikesafterCommand", 0)
            likes_given = data.get("LikesGivenByAPI", 0)
            
            result_text = (
                f"✅ **लाइक सफलतापूर्वक भेज दिए गए!**\n\n"
                f"👤 **नाम:** {player_name}\n"
                f"🆔 **यूआईडी:** `{target_uid}`\n"
                f"❤️ **बढ़े हुए लाइक:** +{likes_given}\n"
                f"📊 **पहले:** {before_likes} ➔ **अब:** {after_likes}"
            )
            bot.edit_message_text(result_text, chat_id=status_msg.chat.id, message_id=status_msg.message_id, parse_mode="Markdown")
        else:
            bot.edit_message_text("❌ सर्वर ने एरर दिया। टोकन एक्सपायर हो सकते हैं।", chat_id=status_msg.chat.id, message_id=status_msg.message_id)

    except requests.exceptions.Timeout:
        bot.edit_message_text("⏱️ टाइमआउट हो गया! गरेना का सर्वर स्लो चल रहा है।", chat_id=status_msg.chat.id, message_id=status_msg.message_id)
    except Exception as e:
        bot.edit_message_text(f"⚠️ एरर आ गया: {e}", chat_id=status_msg.chat.id, message_id=status_msg.message_id)

print("बॉट शुरू हो गया है, लीडर...")
bot.infinity_polling()
