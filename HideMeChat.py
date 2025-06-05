# 🤖 ربات چت ناشناس تلگرام  

##**ارزش سورس گاد**

##ربات چت ناشناس :
##- **چت تصادفی - انتخاب جنسیت**
##- **سیستم دعوا رفال گیری برای سکه**
##- **سیستم دعوت رفال گیری برای پول**
##- **پنل مدیریت پیشرفته**
##- **عضویت اجباری - همگانی - مدیریت کاربران - مدیریت رفال سکه موجودی پول کاربر - بن ان بن - و........**

## 🛠 پیشنیاز
##- **Python**
##- **pyTelegramBotAPI**
##- **db-sqlite3**
##- **threading**
##- **traceback**

## Telegram : @YoungArvin
## Bale : @YoungArvin
## GitHub : https://github.com/iiiiArvin

## README LICENSE

import telebot
from telebot import types
import sqlite3
import time
import random
import string
import threading
import re
from telebot.types import LabeledPrice
from datetime import datetime, timedelta

TOKEN = ''
ADMIN_IDS = {}
ADMIN_CHAT = 
ADMIN_USERNAME = "" 
LINK = "" # متفیر link رو باید با :  https://t.me/ یا https://ble.ir/ جایگذین کنید. 

bot = telebot.TeleBot(TOKEN)



# --- دیتابیس

db_lock = threading.Lock()

def get_db_connection():

    conn = sqlite3.connect('chat_users.db', check_same_thread=False)
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size = 10000")
    conn.execute("PRAGMA synchronous=NORMAL;") 
    conn.execute("PRAGMA temp_store=MEMORY;")
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS channels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id TEXT NOT NULL,
        title TEXT,
        invite_link TEXT,
        expire_at DATETIME
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        coin_balance INTEGER DEFAULT 10,
        balance INTEGER DEFAULT 0,
        gender TEXT
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS waiting_users (
        user_id INTEGER PRIMARY KEY,
        desired_gender TEXT,
        join_time REAL
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS active_chats (
        user_id INTEGER PRIMARY KEY,
        partner_id INTEGER
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS anonymous_links (
        link_id TEXT PRIMARY KEY,
        user_id INTEGER
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS referral_links (
        referral_code TEXT PRIMARY KEY,
        user_id INTEGER
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS used_referrals (
        user_id INTEGER,
        referral_code TEXT,
        PRIMARY KEY (user_id, referral_code)
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS pending_referrals (
        user_id INTEGER PRIMARY KEY,
        referral_code TEXT,
        timestamp REAL
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS blocked_users (
        blocker_id INTEGER,
        blocked_id INTEGER,
        PRIMARY KEY (blocker_id, blocked_id)
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS last_chat (
        user_id INTEGER PRIMARY KEY,
        partner_id INTEGER
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS banned_users (
        user_id INTEGER PRIMARY KEY,
        ban_reason TEXT
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS pending_disconnect (
        user_id INTEGER PRIMARY KEY,
        pending INTEGER DEFAULT 0
    )
    ''')

    conn.commit()
    conn.close()

init_db()

# --- توابع کمکی

def add_new_user(user_id):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()
        conn.close()

def generate_random_code(length=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def get_referral_code(user_id):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT referral_code FROM referral_links WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        if row:
            code = row[0]
        else:
            code = generate_random_code()
            cursor.execute('INSERT INTO referral_links (referral_code, user_id) VALUES (?, ?)', (code, user_id))
            conn.commit()
        conn.close()
    return code

def get_anonymous_link(user_id):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT link_id FROM anonymous_links WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        if row:
            link_id = row[0]
        else:
            link_id = generate_random_code()
            cursor.execute('INSERT INTO anonymous_links (link_id, user_id) VALUES (?, ?)', (link_id, user_id))
            conn.commit()
        conn.close()
    return link_id

def remove_active_chat(user_id):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT partner_id FROM active_chats WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        partner_id = None
        if row:
            partner_id = row[0]
            cursor.execute('DELETE FROM active_chats WHERE user_id IN (?, ?)', (user_id, partner_id))
            cursor.execute('INSERT OR REPLACE INTO last_chat (user_id, partner_id) VALUES (?, ?)', (user_id, partner_id))
            cursor.execute('INSERT OR REPLACE INTO last_chat (user_id, partner_id) VALUES (?, ?)', (partner_id, user_id))
            conn.commit()
        conn.close()
    return partner_id

def is_user_banned(user_id):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM banned_users WHERE user_id = ?', (user_id,))
        banned = cursor.fetchone() is not None
        conn.close()
    return banned

def get_user_coin_balance(user_id):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT coin_balance FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
    if result:
        return result[0]
    else:
        return 0

def is_in_active_chat(user_id):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT partner_id FROM active_chats WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
    return result is not None

# --- منو

def get_inline_main_menu():
    markup = types.InlineKeyboardMarkup()
    btn_start = types.InlineKeyboardButton("شروع چت", callback_data="start_chat")
    btn_invite = types.InlineKeyboardButton("لینک دعوت", callback_data="referral_link")
    btn_anon = types.InlineKeyboardButton("لینک ناشناس", callback_data="anon_link")
    btn_buy = types.InlineKeyboardButton("خرید سکه", callback_data="buy_coins")
    btn_help = types.InlineKeyboardButton("راهنما", callback_data="help")
    btn_support = types.InlineKeyboardButton("پشتیبانی", callback_data="support")
    markup.add(btn_anon, btn_invite)
    markup.add(btn_support, btn_buy)
    markup.add(btn_help)
    markup.add(btn_start)
    return markup

def get_buy_coins_menu():
    keyboard = types.InlineKeyboardMarkup()
    coin10 = types.InlineKeyboardButton("خرید 10 سکه", callback_data="coin_10")
    coin20 = types.InlineKeyboardButton("خرید 20 سکه", callback_data="coin_20")
    keyboard.add(coin10, coin20)
    coin50 = types.InlineKeyboardButton("خرید 50 سکه", callback_data="coin_50")
    coin80 = types.InlineKeyboardButton("خرید 80 سکه", callback_data="coin_80")
    keyboard.add(coin50, coin80)
    coin100 = types.InlineKeyboardButton("خرید 100 سکه", callback_data="coin_100")
    keyboard.add(coin100)
    btn_back = types.InlineKeyboardButton("بازگشت", callback_data="back_main")
    keyboard.add(btn_back)
    return keyboard

def get_inline_gender_selection():
    markup = types.InlineKeyboardMarkup()
    btn_female = types.InlineKeyboardButton("دختر", callback_data="set_gender_دختر")
    btn_male = types.InlineKeyboardButton("پسر", callback_data="set_gender_پسر")
    markup.add(btn_female, btn_male)
    return markup

def get_inline_partner_preference():
    markup = types.InlineKeyboardMarkup()
    btn_female = types.InlineKeyboardButton("دختر", callback_data="pref_دختر")
    btn_male = types.InlineKeyboardButton("پسر", callback_data="pref_پسر")
    btn_any = types.InlineKeyboardButton("مهم نیست", callback_data="pref_مهم_نیست")
    btn_back = types.InlineKeyboardButton("بازگشت", callback_data="back_main")
    markup.add(btn_female, btn_male)
    markup.add(btn_back)
    markup.add(btn_any)
    return markup

def get_reply_active_chat_keyboard():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add("قطع چت")
    return markup

def get_reply_confirm_keyboard():
    markup = types.InlineKeyboardMarkup()
    btn_confirm = types.InlineKeyboardButton("بله", callback_data="confirm_stop")
    btn_cancel = types.InlineKeyboardButton("نه", callback_data="cancel_stop_in_chat")
    markup.add(btn_confirm, btn_cancel)
    return markup

def get_post_chat_menu():
    markup = types.InlineKeyboardMarkup()
    bleck = types.InlineKeyboardButton("بلاک کردن کاربر", callback_data="bleck")
    report = types.InlineKeyboardButton("گزارش", callback_data="report")
    btn_cancel = types.InlineKeyboardButton("عدم اقدام", callback_data="nthing")
    markup.add(bleck, report)
    markup.add(btn_cancel)
    return markup

@bot.message_handler(func=lambda message: message.text == "قطع چت" and message.chat.type == "private")
def disconnect_request_handler(message):
    user_id = message.chat.id
    if not is_in_active_chat(user_id):
        bot.send_message(user_id, "شما در چت فعال نیستید.", reply_markup=get_inline_main_menu())
        return
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT OR REPLACE INTO pending_disconnect (user_id, pending) VALUES (?, ?)', (user_id, 1))
        conn.commit()
        conn.close()
    bot.send_message(user_id, "آیا مطمئن هستید که می‌خواهید چت را قطع کنید؟", reply_markup=get_reply_confirm_keyboard())

@bot.callback_query_handler(func=lambda call: call.data == "cancel_stop_in_chat"and call.message.chat.type == "private")
def cancel_stop_in_chat(call):
    user_id = call.from_user.id
    if not is_in_active_chat(user_id):
        bot.send_message(user_id, "شما در چت فعال نیستید.", reply_markup=get_inline_main_menu())
        return
    bot.edit_message_text("باشه به چت ادامه بده :)",user_id,call.message.message_id,reply_markup=get_reply_active_chat_keyboard())

@bot.callback_query_handler(func=lambda call: call.data == "confirm_stop"and call.message.chat.type == "private")
def confirm_stop(call):
    user_id = call.from_user.id
    if not is_in_active_chat(user_id):
        bot.send_message(user_id, "شما در چت فعال نیستید.", reply_markup=get_inline_main_menu())
        return
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT pending FROM pending_disconnect WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close() 

    if not result or result[0] != 1:
        bot.send_message(user_id, "عملیات نامعتبره\n\nبرای قطع کردن چت از دکمه *قطع چت* استفاده کنید\n\nهمچنین میتوانید تایپ کنید: *قطع چت*",reply_markup=get_reply_active_chat_keyboard())
        return

    partner_id = remove_active_chat(user_id)
    if partner_id:
        bot.edit_message_text(
            "شما چت را قطع کردید.",
            chat_id=user_id,
            message_id=call.message.message_id,
            reply_markup=get_post_chat_menu()
        )
        bot.send_message(partner_id, "کاربر مقابل چت را قطع کرد. چت به پایان رسید.", reply_markup=get_post_chat_menu())
    else:
        with db_lock:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM waiting_users WHERE user_id = ?', (user_id,))
            conn.commit()
            conn.close()
        bot.edit_message_text(
            "از حالت انتظار خارج شدید.",
            chat_id=user_id,
            message_id=call.message.message_id,
            reply_markup=get_inline_main_menu()
        )

    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM pending_disconnect WHERE user_id = ?', (user_id,))
        conn.commit()
        conn.close()

def get_inline_waiting_menu():
    markup = types.InlineKeyboardMarkup()
    btn_stop_wait = types.InlineKeyboardButton("قطع انتظار", callback_data="disconnect_waiting")
    markup.add(btn_stop_wait)
    return markup

def check_user_gender(user_id):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT coin_balance, gender FROM users WHERE user_id = ?', (user_id,))
        data = cursor.fetchone()

        if not data:
            cursor.execute('INSERT INTO users (user_id, coin_balance) VALUES (?, ?)', (user_id, 10))
            conn.commit()
            conn.close()
            bot.send_message(
                user_id,
                "به ربات چت ناشناس خوش آمدید!\n\nلطفاً جنسیت خود را انتخاب کنید:",
                reply_markup=get_inline_gender_selection()
            )
            return False

        coin_balance, gender = data
        conn.close()
        if gender is None:
            bot.send_message(
                user_id,
                "لطفاً ابتدا جنسیت خود را انتخاب کنید:",
                reply_markup=get_inline_gender_selection()
            )
            return False
    return True

def add_channel(chat_id, title, invite_link, expire_at):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO channels (chat_id, title, invite_link, expire_at)
        VALUES (?, ?, ?, ?)
    """, (chat_id, title, invite_link, expire_at))
    conn.commit()
    conn.close()

def get_active_channels():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT chat_id, invite_link, title FROM channels WHERE datetime(expire_at) > datetime('now')")
    channels = cur.fetchall()
    conn.close()
    return channels

def check_channel_membership(chat_id, user_id):
    try:
        member = bot.get_chat_member(chat_id=chat_id, user_id=user_id)
        return member.status in ["creator", "administrator", "member"]
    except Exception:
        return False

def check_channels(user_id, msg):
    if msg is None:
        msg = ""
        
    channels = get_active_channels()

    
    not_member_channels = []
    for chat_id, invite_link, title in channels:
        is_member = check_channel_membership(chat_id, user_id)
       
        if not is_member:
            not_member_channels.append((chat_id, invite_link, title))
    
    if not_member_channels:
        markup = types.InlineKeyboardMarkup()
        buttons = [types.InlineKeyboardButton(title, url=invite_link) 
                   for _, invite_link, title in not_member_channels]
        markup.row(*buttons)

        vry = types.InlineKeyboardButton("تأیید عضویت", callback_data=f"verify_membership_{msg}")
        markup.add(vry)
        
        channels_list = "\n".join([f"• {title}" for _, _, title in not_member_channels])
        bot.send_message(
            user_id,
            "⚠️ برای استفاده از ربات باید در کانال‌های زیر عضو شوید:\n"
            f"{channels_list}\n"
            "پس از عضویت روی دکمه «تأیید عضویت» کلیک کنید:",
            reply_markup=markup
        )
        return False
    return True

@bot.callback_query_handler(func=lambda call: call.data.startswith("verify_membership_")and call.message.chat.type == "private")
def verify_membership(call):
    user_id = call.from_user.id
    add_new_user(user_id)
    message_id = call.message.message_id
    re = (call.data.split("_")[2])
    if not check_channels(user_id,msg=None):
        bot.send_message(user_id, "❌ شما هنوز عضو کانال نشده‌اید!")
        return
    bot.edit_message_text(
        chat_id=user_id,
        message_id=message_id,
        text="✅ عضویت شما با موفقیت تأیید شد!",
        reply_markup=None
    )
    if re.startswith("/start ref-"):
        referral_code = re.split("ref-")[-1].strip()
        referral_handler(user_id,referral_code)
        return
    if re.startswith("/start send-"):  
        link_id = re.split("send-")[-1].strip()  
        anonymous_send_handler(user_id,link_id)
        return
    
# --- استارت

@bot.message_handler(commands=['start'],chat_types=["private"])
def start_handler(message):
    user_id = message.chat.id
    add_new_user(user_id)
    msg = message.text
    if not check_channels(user_id,msg):
        return
    if is_user_banned(user_id):
        bot.send_message(user_id, "شما بن شده‌اید.")
        return
    if is_user_banned(user_id):
        bot.send_message(user_id, "شما بن شده‌اید.")
        return
    if message.text.startswith("/start ref-"):
        referral_code = message.text.split("ref-")[-1].strip()
        referral_handler(user_id,referral_code)
        return
    if message.text.startswith("/start send-"):  
        link_id = message.text.split("send-")[-1].strip()  
        anonymous_send_handler(user_id,link_id)
        return
    if is_in_active_chat(user_id):
        bot.send_message(user_id, "شما در چت فعال هستید. ابتدا چت فعلی را به پایان دهید.",reply_markup=get_reply_confirm_keyboard())
        return
    if is_user_in_waiting(user_id): 
        bot.send_message(user_id,"شما ابتدا باید حالت انتظار را لغو کنید سپس")
        return
    welcome_text = (
        "به ربات چت ناشناس خوش آمدید!\n\n"
        "برای شروع چت از دکمه «شروع چت» استفاده کنید.\n"
        f"موجودی سکه شما: {get_user_coin_balance(user_id)} 🪙\n"
        f"شناسه کاربری: {user_id} 👤"
    )
    bot.send_message(user_id, welcome_text, reply_markup=get_inline_main_menu())

# --- جنسیت

@bot.callback_query_handler(func=lambda call: call.data.startswith("set_gender_")and call.message.chat.type == "private")
def gender_callback(call):
    user_id = call.from_user.id
    if is_user_banned(user_id):
        bot.send_message(user_id, "شما بن شده‌اید.")
        return
    if is_user_in_waiting(user_id):  
        bot.send_message(user_id,"شما ابتدا باید حالت انتظار را لغو کنید سپس")
        return
    if is_in_active_chat(user_id):
        bot.send_message(user_id, "شما در چت فعال هستید. ابتدا چت فعلی را به پایان دهید.",reply_markup=get_reply_confirm_keyboard())
        return
    gender = call.data.split("_")[-1]
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET gender = ? WHERE user_id = ?', (gender, user_id))
        conn.commit()
        conn.close()
   
    bot.edit_message_text("منوی اصلی:", chat_id=user_id, message_id=call.message.message_id,
                          reply_markup=get_inline_main_menu())

@bot.callback_query_handler(func=lambda call: call.data == "referral_link"and call.message.chat.type == "private")
def referral_link1(call):
    user_id = call.from_user.id
    add_new_user(user_id)
    if is_user_banned(user_id):
        bot.send_message(user_id, "شما بن شده‌اید.")
        return
    if is_user_in_waiting(user_id): 
        bot.send_message(user_id,"شما ابتدا باید حالت انتظار را لغو کنید سپس")
        return
    if is_in_active_chat(user_id):
        bot.edit_message_text("شما در چت فعال هستید. ابتدا چت فعلی را به پایان دهید.", chat_id=user_id, message_id=call.message.message_id,
                          reply_markup=get_reply_confirm_keyboard())
        return
    if not check_channels(user_id,msg=None):
        return
    code = get_referral_code(user_id)
    referral_link = f"https://{LINK}/{bot.get_me().username}?start=ref-{code}"
    bot.edit_message_text(f"🔗 لینک دعوت شما:\n{referral_link}\n\nبا هر دعوت موفق 2 سکه دریافت کنید!", chat_id=user_id, message_id=call.message.message_id,
                          reply_markup=get_inline_main_menu())
    
@bot.callback_query_handler(func=lambda call: call.data == "anon_link"and call.message.chat.type == "private")
def anon_link1(call):
    user_id = call.from_user.id
    add_new_user(user_id)
    if is_user_banned(user_id):
        bot.send_message(user_id, "شما بن شده‌اید.")
        return
    if is_user_in_waiting(user_id): 
        bot.send_message(user_id,"شما ابتدا باید حالت انتظار را لغو کنید سپس")
        return
    if is_in_active_chat(user_id):
        bot.edit_message_text("شما در چت فعال هستید. ابتدا چت فعلی را به پایان دهید.", chat_id=user_id, message_id=call.message.message_id,
                          reply_markup=get_reply_confirm_keyboard())
        return
    if not check_channels(user_id,msg=None):
        return
    link_id = get_anonymous_link(user_id)
    anon_link = f"https://{LINK}/{bot.get_me().username}?start=send-{link_id}"
    bot.edit_message_text(f"🔗 لینک ناشناس شما:\n{anon_link}\n\nهرکس این لینک را باز کند می‌تواند به شما پیام ناشناس ارسال کند!", chat_id=user_id, message_id=call.message.message_id,
                          reply_markup=get_inline_main_menu())
    
# --- این بخش برای بله در دسترسه

@bot.callback_query_handler(func=lambda call: call.data.startswith("coin_")and call.message.chat.type == "private")
def gender1_callback(call):
    user_id = call.from_user.id
    add_new_user(user_id)
    if is_user_banned(user_id):
        bot.send_message(user_id, "شما بن شده‌اید.")
        return
    if is_user_in_waiting(user_id):
        bot.send_message(user_id,"شما ابتدا باید حالت انتظار را لغو کنید سپس")
        return
    if is_in_active_chat(user_id):
        bot.send_message(user_id, "شما در چت فعال هستید. ابتدا چت فعلی را به پایان دهید.", reply_markup=get_reply_confirm_keyboard())
        return
    if not check_channels(user_id,msg=None):
        return

    coin = int(call.data.split("_")[-1])
    price = get_coin_price(coin) 

    if price is not None:
        amount_in_toman = price  
        amount_in_rial = amount_in_toman * 10  
        labeled_price = LabeledPrice(label=f"{coin}", amount=amount_in_rial)
        
        payload = f"{user_id}:{coin}"
        
        bot.send_invoice(
            user_id,
            title=f"خرید {coin} سکه",
            currency="IRR",
            description="شارژ حساب کاربری در ربات",
            provider_token="شماره کارت",
            prices=[labeled_price],  
            invoice_payload=payload
        )

    else:
            bot.send_message(user_id, "مقدار سکه معتبر نیست.")

def get_coin_price(coin):
    """تابعی برای دریافت قیمت بر اساس تعداد سکه"""
    coin_prices = {
        10: 2500,  
        20: 5000,  
        50: 7500,  
        80: 10000,  
        100: 15000
    }
    return coin_prices.get(coin)

@bot.message_handler(content_types=["successful_payment"],chat_types=["private"])
def successful_payment_handler(message):
    sp = message.successful_payment
    prices = sp.total_amount
    payload_parts = sp.invoice_payload.split(":")
    user_id = int(payload_parts[0])
    purchased_coins = int(payload_parts[1])


    add_coins_to_user_account(user_id=user_id, coin=purchased_coins,prices=prices)

def add_coins_to_user_account(user_id, coin, prices):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET coin_balance = coin_balance + ? WHERE user_id = ?", (coin, user_id))
        conn.commit()
        conn.close()
    bot.send_message(
    user_id,
    f"✨ *شارژ حساب شما انجام شد*\n\n"
    f"🔹 *سکه:* {coin} +\n"
    f"🔸 *مبلغ پرداختی:* {prices} ریال"
    )


@bot.callback_query_handler(func=lambda call: call.data == "buy_coins"and call.message.chat.type == "private")
def buy_coins1(call):
    user_id = call.from_user.id
    if is_user_banned(user_id):
        bot.send_message(user_id, "شما بن شده‌اید.")
        return
    if is_user_in_waiting(user_id):  
        bot.send_message(user_id,"شما ابتدا باید حالت انتظار را لغو کنید سپس")
        return
    if is_in_active_chat(user_id):
        bot.edit_message_text("شما در چت فعال هستید. ابتدا چت فعلی را به پایان دهید.", chat_id=user_id, message_id=call.message.message_id,
                          reply_markup=get_reply_confirm_keyboard())
        return
    if not check_channels(user_id,msg=None):
        return
    bot.edit_message_text(f"خرید سکه \nامکان شارژ حساب با پاکت امکان پذیره برای شارژ حساب با پاکت به ای دی زیر مراجعه کنید.\n{ADMIN_USERNAME}:", chat_id=user_id, message_id=call.message.message_id,
                          reply_markup=get_buy_coins_menu())

# --- ادامه کد

@bot.callback_query_handler(func=lambda call: call.data == "support"and call.message.chat.type == "private")
def support1(call):
    user_id = call.from_user.id
    if is_user_banned(user_id):
        bot.send_message(user_id, "شما بن شده‌اید.")
        return
    if is_user_in_waiting(user_id):  
        bot.send_message(user_id,"شما ابتدا باید حالت انتظار را لغو کنید سپس")
        return
    if is_in_active_chat(user_id):
        bot.edit_message_text("شما در چت فعال هستید. ابتدا چت فعلی را به پایان دهید.", chat_id=user_id, message_id=call.message.message_id,
                          reply_markup=get_reply_confirm_keyboard())
        return
    if not check_channels(user_id,msg=None):
        return
    bot.edit_message_text(f"برای پشتیبانی با ما تماس بگیرید:\nآیدی: {ADMIN_USERNAME}", chat_id=user_id, message_id=call.message.message_id,
                          reply_markup=get_inline_main_menu())
    
@bot.callback_query_handler(func=lambda call: call.data == "help"and call.message.chat.type == "private")
def help1(call):
    user_id = call.from_user.id
    if is_user_banned(user_id):
        bot.send_message(user_id, "شما بن شده‌اید.")
        return
    if is_user_in_waiting(user_id): 
        bot.send_message(user_id,"شما ابتدا باید حالت انتظار را لغو کنید سپس")
        return
    if is_in_active_chat(user_id):
        bot.edit_message_text("شما در چت فعال هستید. ابتدا چت فعلی را به پایان دهید.", chat_id=user_id, message_id=call.message.message_id,
                          reply_markup=get_reply_confirm_keyboard())
        return
    if not check_channels(user_id,msg=None):
        return
    help_text = (
            "راهنما:\n"
            "1. برای شروع چت، روی «شروع چت» کلیک کنید.\n"
            "2. سپس ترجیح مخاطب (دختر، پسر یا مهم نیست) را انتخاب کنید.\n"
            "3. در حین چت، از دکمه «قطع چت» برای پایان استفاده کنید.\n"
            "4. برای پشتیبانی از گزینه «پشتیبانی» استفاده کنید.\n"

        )
    bot.edit_message_text(help_text, chat_id=user_id, message_id=call.message.message_id,
                          reply_markup=get_inline_main_menu())

# --- شروع چت
    
@bot.callback_query_handler(func=lambda call: call.data == "start_chat"and call.message.chat.type == "private")
def start_chat_callback(call):
    user_id = call.from_user.id
    if is_user_banned(user_id):
        bot.send_message(user_id, "شما بن شده‌اید.")
        return
    if is_user_in_waiting(user_id):  
        bot.send_message(user_id,"شما ابتدا باید حالت انتظار را لغو کنید سپس")
        return
    if is_in_active_chat(user_id):
        
        bot.edit_message_text("شما در چت فعال هستید. ابتدا چت فعلی را به پایان دهید.", chat_id=user_id, message_id=call.message.message_id,
                          reply_markup=get_reply_confirm_keyboard())
        return
    if not check_channels(user_id,msg=None):
        return

    coin_balance = get_user_coin_balance(user_id)
    if coin_balance < 1:
        bot.edit_message_text(" ",user_id,call.message.message_id,reply_markup=get_buy_coins_menu())
        return 
    if not check_user_gender(user_id):
        return 
    bot.edit_message_text("لطفاً ترجیح شریک خود را انتخاب کنید:",user_id,call.message.message_id,reply_markup=get_inline_partner_preference())
    
@bot.callback_query_handler(func=lambda call: call.data.startswith("pref_")and call.message.chat.type == "private")
def partner_pref_callback(call):
    user_id = call.from_user.id
    if is_user_banned(user_id):
        bot.send_message(user_id, "شما بن شده‌اید.")
        return
    if is_user_in_waiting(user_id): 
        bot.send_message(user_id,"شما ابتدا باید حالت انتظار را لغو کنید سپس")
        return
    if is_in_active_chat(user_id):
        bot.edit_message_text("شما در چت فعال هستید. ابتدا چت فعلی را به پایان دهید.", chat_id=user_id, message_id=call.message.message_id,
                          reply_markup=get_reply_confirm_keyboard())
        return
    if not check_channels(user_id,msg=None):
        return
    pref = call.data.split("_")[-1]
    if pref == "مهم":
        pref = "مهم نیست"
    join_time = time.time()
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT OR REPLACE INTO waiting_users (user_id, desired_gender, join_time) VALUES (?, ?, ?)',
                       (user_id, pref, join_time))
        conn.commit()
        conn.close()
    waiting_message = bot.edit_message_text("در حال انتظار برای پیدا شدن شریک چت...", chat_id=user_id,
                                              message_id=call.message.message_id, reply_markup=get_inline_waiting_menu())
    waiting_message_id = waiting_message.edit_date

    threading.Thread(target=find_match_for_user, args=(user_id, waiting_message_id,)).start()

@bot.callback_query_handler(func=lambda call: call.data == "back_main"and call.message.chat.type == "private")
def back_main_callback(call):
    user_id = call.from_user.id
    if is_user_banned(user_id):
        bot.send_message(user_id, "شما بن شده‌اید.")
        return
    if is_user_in_waiting(user_id):  
        bot.send_message(user_id,"شما ابتدا باید حالت انتظار را لغو کنید سپس")
        return
    if is_in_active_chat(user_id):
        bot.edit_message_text("شما در چت فعال هستید. ابتدا چت فعلی را به پایان دهید.", chat_id=user_id, message_id=call.message.message_id,
                          reply_markup=get_reply_confirm_keyboard())
        return
    if not check_channels(user_id,msg=None):
        return
    bot.edit_message_text("منوی اصلی:", chat_id=user_id, message_id=call.message.message_id,
                          reply_markup=get_inline_main_menu())

# --- پیدا کردن شریک

def is_compatible(user_a, pref_a, user_b, pref_b, user_id, candidate_id):
    cond_a = (pref_a == "مهم نیست") or (user_b == pref_a)
    cond_b = (pref_b == "مهم نیست") or (user_a == pref_b)
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM blocked_users WHERE blocker_id = ? AND blocked_id = ?', (user_id, candidate_id))
        if cursor.fetchone():
            conn.close()
            return False
        cursor.execute('SELECT 1 FROM blocked_users WHERE blocker_id = ? AND blocked_id = ?', (candidate_id, user_id))
        if cursor.fetchone():
            conn.close()
            return False
        conn.close()
    return cond_a and cond_b

def find_match_for_user(user_id, waiting_message_id):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT gender, coin_balance FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        if not result:
            conn.close()
            return
        user_gender, coin_balance = result
        cursor.execute('SELECT desired_gender FROM waiting_users WHERE user_id = ?', (user_id,))
        res = cursor.fetchone()
        if not res:
            conn.close()
            return
        my_pref = res[0]
        cursor.execute('SELECT user_id, desired_gender FROM waiting_users WHERE user_id != ?', (user_id,))
        candidates = cursor.fetchall()
        conn.close()

    for candidate in candidates:
        candidate_id, candidate_pref = candidate
        with db_lock:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT gender, coin_balance FROM users WHERE user_id = ?', (candidate_id,))
            candidate_info = cursor.fetchone()
            conn.close()
        if not candidate_info:
            continue
        candidate_gender, candidate_coins = candidate_info
        if coin_balance < 2 or candidate_coins < 2:
            continue
        if is_compatible(user_gender, my_pref, candidate_gender, candidate_pref, user_id, candidate_id):
            
            with db_lock:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute('INSERT OR REPLACE INTO active_chats (user_id, partner_id) VALUES (?, ?)', (user_id, candidate_id))
                cursor.execute('INSERT OR REPLACE INTO active_chats (user_id, partner_id) VALUES (?, ?)', (candidate_id, user_id))
                cursor.execute('DELETE FROM waiting_users WHERE user_id IN (?, ?)', (user_id, candidate_id))
                
                cursor.execute("UPDATE users SET coin_balance = coin_balance - 2 WHERE user_id = ?", (user_id,))
                cursor.execute("UPDATE users SET coin_balance = coin_balance - 2 WHERE user_id = ?", (candidate_id,))
                conn.commit()
                conn.close()
            
            try:
                bot.delete_message(user_id, waiting_message_id)
            except Exception as e:
                pass
            bot.edit_message_text("شما با یک کاربر پیدا شدید. شروع چت!", user_id, waiting_message_id)
            bot.send_message(user_id, "شما با یک کاربر پیدا شدید. شروع چت!", reply_markup=get_reply_active_chat_keyboard())
            bot.send_message(candidate_id, "شما با یک کاربر پیدا شدید. شروع چت!", reply_markup=get_reply_active_chat_keyboard())
            return
        
    for candidate in candidates:
        candidate_id, candidate_pref = candidate
        with db_lock:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT gender, coin_balance FROM users WHERE user_id = ?', (candidate_id,))
            candidate_info = cursor.fetchone()
            conn.close()
        if not candidate_info:
            continue
        candidate_gender, candidate_coins = candidate_info
        if coin_balance < 1 or candidate_coins < 1:
            continue
        with db_lock:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT 1 FROM blocked_users WHERE blocker_id = ? AND blocked_id = ?', (user_id, candidate_id))
            if cursor.fetchone():
                conn.close()
                continue
            cursor.execute('SELECT 1 FROM blocked_users WHERE blocker_id = ? AND blocked_id = ?', (candidate_id, user_id))
            if cursor.fetchone():
                conn.close()
                continue
            conn.close()
        
        with db_lock:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('INSERT OR REPLACE INTO active_chats (user_id, partner_id) VALUES (?, ?)', (user_id, candidate_id))
            cursor.execute('INSERT OR REPLACE INTO active_chats (user_id, partner_id) VALUES (?, ?)', (candidate_id, user_id))
            cursor.execute('DELETE FROM waiting_users WHERE user_id IN (?, ?)', (user_id, candidate_id))

            cursor.execute("UPDATE users SET coin_balance = coin_balance - 1 WHERE user_id = ?", (user_id,))
            cursor.execute("UPDATE users SET coin_balance = coin_balance - 1 WHERE user_id = ?", (candidate_id,))
            conn.commit()
            conn.close()
        try:
            bot.delete_message(user_id, waiting_message_id)
        except Exception as e:
            pass
        bot.send_message(user_id, "شما با یک کاربر پیدا شدید. شروع چت!", reply_markup=get_reply_active_chat_keyboard())
        bot.send_message(candidate_id, "شما با یک کاربر پیدا شدید. شروع چت!", reply_markup=get_reply_active_chat_keyboard())
        return

# --- قطع چت

@bot.callback_query_handler(func=lambda call: call.data == "disconnect_waiting"and call.message.chat.type == "private")
def disconnect_callback(call):
    user_id = call.from_user.id
    if not (is_in_active_chat(user_id) or is_user_in_waiting(user_id)):
        bot.edit_message_text("باش", chat_id=user_id, message_id=call.message.message_id)
        return
        
    if is_in_active_chat(user_id):
            bot.edit_message_text("شما در چت فعال هستید. ابتدا چت فعلی را به پایان دهید.", chat_id=user_id, message_id=call.message.message_id,
                          reply_markup=get_reply_confirm_keyboard())
            return
    with db_lock:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('DELETE FROM waiting_users WHERE user_id = ?', (user_id,))
            conn.commit()
            conn.close()
            bot.edit_message_text("از حالت انتظار خارج شدید.",user_id,call.message.message_id,reply_markup=get_inline_main_menu())

@bot.callback_query_handler(func=lambda call: call.data == "disconnect_chat"and call.message.chat.type == "private")
def disconnect_chat(call):
    user_id = call.from_user.id
    bot.edit_message_text("آیا مطمئن هستید که می‌خواهید چت را قطع کنید؟", 
                              chat_id=user_id, 
                              message_id=call.message.message_id,
                              reply_markup=get_reply_confirm_keyboard())
    
@bot.callback_query_handler(func=lambda call: call.data == "cancel_stop"and call.message.chat.type == "private")
def cancel_stop(call):
    user_id = call.from_user.id
    bot.edit_message_text("منوی چت فعال:", chat_id=user_id, message_id=call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data == "bleck"and call.message.chat.type == "private")
def bleck1(call):
    user_id = call.from_user.id
    try:
        with db_lock:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT partner_id FROM last_chat WHERE user_id = ?', (user_id,))
            last = cursor.fetchone()
            partner_id = last[0]
            cursor.execute('INSERT OR REPLACE INTO blocked_users (blocker_id, blocked_id) VALUES (?, ?)', (user_id, partner_id))
            conn.commit()
            bot.edit_message_text("کاربر مورد نظر بلاک شد. از این پس دیگر با او جفت نخواهید شد.", chat_id=user_id, message_id=call.message.message_id, reply_markup=get_inline_main_menu())
    except:
        bot.edit_message_text("کاربر مورد نظر بلاک شد. از این پس دیگر با او جفت نخواهید شد.", chat_id=user_id, message_id=call.message.message_id, reply_markup=get_inline_main_menu())     
          
@bot.callback_query_handler(func=lambda call: call.data == "report" and call.message.chat.type == "private")
def report1(call):
    user_id = call.from_user.id
    try:
        with db_lock:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT partner_id FROM last_chat WHERE user_id = ?', (user_id,))
            last = cursor.fetchone()

            if not last:
                bot.edit_message_text("چت فعالی برای گزارش پیدا نشد.", chat_id=user_id, message_id=call.message.message_id)
                return

            partner_id = last[0]

            cursor.execute('''
                CREATE TABLE IF NOT EXISTS reports (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    reporter_id INTEGER,
                    reported_id INTEGER,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('INSERT INTO reports (reporter_id, reported_id) VALUES (?, ?)', (user_id, partner_id))

            cursor.execute('SELECT COUNT(*) FROM reports WHERE reported_id = ?', (partner_id,))
            count = cursor.fetchone()[0]
            conn.commit()
            conn.close()

            report_text = f"📩 گزارش: کاربر {user_id}، کاربر {partner_id} را گزارش کرده است. (تعداد کل گزارش‌ها: {count})"
            bot.send_message(ADMIN_CHAT, report_text)

            if count >= 5:
                bot.send_message(ADMIN_CHAT, f"⚠️ هشدار: کاربر {partner_id} بیش از ۵ بار گزارش شده است!")

            bot.edit_message_text("✅ گزارش شما به مدیریت ارسال شد.", chat_id=user_id, message_id=call.message.message_id, reply_markup=get_inline_main_menu())

    except Exception as e:
        print("Report Error:", e)
        bot.edit_message_text("گزارش شما ثبت نشد. لطفاً دوباره تلاش کنید.", chat_id=user_id, message_id=call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data == "nthing"and call.message.chat.type == "private")
def nthing1(call):
    user_id = call.from_user.id
    bot.edit_message_text("منوی اصلی", chat_id=user_id, message_id=call.message.message_id, reply_markup=get_inline_main_menu())       

def is_user_in_waiting(user_id):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM waiting_users WHERE user_id = ?', (user_id,))
        exists = cursor.fetchone() is not None
        conn.close()
    return exists

link_pattern = re.compile(
    r'((?:https?|ftp):\/\/[^\s/$.?#].[^\s]*)|'    
    r'((?:www\.)[^\s/$.?#].[^\s]*)|'              
    r'(\b(?:[a-z0-9-]+\.)+(?:com|net|org|ir|info|biz|edu|gov|co|io|ai)\b)', 
    re.IGNORECASE
)

# ---  رد بدل پیام

@bot.message_handler(content_types=['text'])
def relay_message(message):
    user_id = message.chat.id
    if message.text == "admin1": # سازنده اصلی
        admin_panel(message)
        return
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT partner_id FROM active_chats WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
    if row:
        if message.text and link_pattern.search(message.text):
            bot.send_message(message.chat.id, "ارسال لینک مجاز نیست!")
            return
        partner_id = row[0]
        try:
            bot.send_message(partner_id, message.text)
        except Exception as e:
            bot.send_message(user_id, "خطا در ارسال پیام به کاربر مقابل.")

# ---  هندل لینک ناشناس

@bot.message_handler(content_types=['photo', 'video', 'animation', 'document', 'audio', 'voice', 'sticker'],chat_types=["private"])
def relay_media(message):
    user_id = message.chat.id   
    if is_user_banned(user_id):
        bot.send_message(user_id, "شما بن شده‌اید.")
        return
    if message.caption and link_pattern.search(message.caption):
        bot.send_message(message.chat.id, "ارسال لینک مجاز نیست!")
        return
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT partner_id FROM active_chats WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
    if row:
        partner_id = row[0]
        try:
            if message.content_type == 'photo':
                bot.send_photo(partner_id, message.photo[-1].file_id, caption=message.caption)
            elif message.content_type == 'video':
                bot.send_video(partner_id, message.video.file_id, caption=message.caption)
            elif message.content_type == 'animation':
                bot.send_animation(partner_id, message.animation.file_id, caption=message.caption)
            elif message.content_type == 'sticker':
                bot.send_sticker(partner_id, message.sticker.file_id)
            elif message.content_type == 'document':
                if message.document.mime_type == 'image/gif':
                    bot.send_animation(partner_id, message.document.file_id, caption=message.caption)
                else:
                    bot.send_document(partner_id, message.document.file_id, caption=message.caption)
                    
            elif message.content_type == 'audio':
                bot.send_audio(partner_id, message.audio.file_id, caption=message.caption)
            elif message.content_type == 'voice':
                bot.send_voice(partner_id, message.voice.file_id, caption=message.caption)
        except Exception as e:
            bot.send_message(user_id, "خطا در ارسال رسانه به کاربر مقابل.")

def anonymous_send_handler(user_id, link_id):
    add_new_user(user_id)
    if is_user_banned(user_id):
        bot.send_message(user_id, "شما بن شده‌اید.")
        return
    if is_user_in_waiting(user_id): 
        bot.send_message(user_id,"شما ابتدا باید حالت انتظار را لغو کنید سپس")
        return
    if is_in_active_chat(user_id):
        bot.send_message(user_id,"شما در چت فعال هستید. ابتدا چت فعلی را به پایان دهید.",
                          reply_markup=get_reply_confirm_keyboard())
        return
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM anonymous_links WHERE link_id = ?', (link_id,))
        row = cursor.fetchone()
        conn.close()
    if not row:
        bot.send_message(user_id, "❌ لینک نامعتبر است!")
        return
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    cancel_button = types.KeyboardButton("لغو")
    markup.add(cancel_button)

   
    prompt_msg = bot.send_message(user_id, "لطفاً پیام خود (متن یا رسانه) را ارسال کنید:", reply_markup=markup)


    bot.register_next_step_handler(prompt_msg, process_anonymous_message, link_id=link_id)

def process_anonymous_message(message, link_id):
    user_id = message.chat.id
    if is_user_banned(user_id):
        bot.send_message(user_id, "شما بن شده‌اید.")
        return

    if message.text == "لغو":
        bot.send_message(user_id, "❌ ارسال پیام لغو شد.", reply_markup=get_inline_main_menu())
        return

    content_type = message.content_type
    forwarded = False  

    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM anonymous_links WHERE link_id = ?', (link_id,))
        row = cursor.fetchone()
        conn.close()
    if not row:
        bot.send_message(user_id, "❌ لینک نامعتبر است!")
        return
    target_user = row[0]

    try:
        if content_type == 'text':
            anon_text = message.text.strip()
            if not anon_text:
                bot.send_message(user_id, "متن پیام خالی است!", reply_markup=get_inline_main_menu())
                return
            bot.send_message(target_user, f"📩 پیام ناشناس:\n\n{anon_text}")
            forwarded = True

        elif content_type == 'photo':
            caption = message.caption if message.caption else ""
            bot.send_photo(target_user, message.photo[-1].file_id, caption=f"📩 پیام ناشناس:\n\n{caption}")
            forwarded = True

        elif content_type == 'video':
            caption = message.caption if message.caption else ""
            bot.send_video(target_user, message.video.file_id, caption=f"📩 پیام ناشناس:\n\n{caption}")
            forwarded = True

        elif content_type == 'animation':
            caption = message.caption if message.caption else ""
            bot.send_animation(target_user, message.animation.file_id, caption=f"📩 پیام ناشناس:\n\n{caption}")
            forwarded = True

        elif content_type == 'document':
            
            if message.document.mime_type == 'gif':
                caption = message.caption if message.caption else ""
                bot.send_animation(target_user, message.document.file_id, caption=f"📩 پیام ناشناس:\n\n{caption}")
            else:
                caption = message.caption if message.caption else ""
                bot.send_document(target_user, message.document.file_id, caption=f"📩 پیام ناشناس:\n\n{caption}")
            forwarded = True

        elif content_type == 'sticker':
            bot.send_sticker(target_user, message.sticker.file_id)
            forwarded = True

        elif content_type == 'audio':
            caption = message.caption if message.caption else ""
            bot.send_audio(target_user, message.audio.file_id, caption=f"📩 پیام ناشناس:\n\n{caption}")
            forwarded = True

        elif content_type == 'voice':
            caption = message.caption if message.caption else ""
            bot.send_voice(target_user, message.voice.file_id, caption=f"📩 پیام ناشناس:\n\n{caption}")
            forwarded = True

        else:
            bot.send_message(user_id, "فرمت این پیام پشتیبانی نمی‌شود.", reply_markup=get_inline_main_menu())
            return

    except Exception as e:
        bot.send_message(user_id, "خطا در ارسال پیام ناشناس به کاربر مقابل.")
        return

    if forwarded:
        bot.send_message(user_id, "✅ پیام شما ارسال شد!", reply_markup=get_inline_main_menu())

# ---  هندل رفال

def referral_handler(user_id,referral_code):
    add_new_user(user_id)
    if is_user_in_waiting(user_id):
        bot.send_message(user_id,"شما ابتدا باید حالت انتظار را لغو کنید سپس")
        return
    if is_in_active_chat(user_id):
        bot.send_message(user_id,"شما در چت فعال هستید. ابتدا چت فعلی را به پایان دهید.",
                          reply_markup=get_reply_confirm_keyboard())
        return
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT user_id FROM referral_links WHERE referral_code = ?', (referral_code,))
        row = cursor.fetchone()
        if row and row[0] != user_id:
            cursor.execute('SELECT 1 FROM used_referrals WHERE user_id = ? AND referral_code = ?', (user_id, referral_code))
            if not cursor.fetchone():
                cursor.execute('INSERT INTO used_referrals (user_id, referral_code) VALUES (?, ?)', (user_id, referral_code))
                cursor.execute('UPDATE users SET coin_balance = coin_balance + 2 WHERE user_id = ?', (row[0],))
                cursor.execute('DELETE FROM pending_referrals WHERE user_id = ?', (user_id,))
                conn.commit()
                bot.send_message(user_id, "✅ 2 سکه به کاربر دعوت‌کننده اضافه شد.", reply_markup=get_inline_main_menu())
            else:
                bot.send_message(user_id, "شما قبلاً از این کد استفاده کرده‌اید.")
        else:
            bot.send_message(user_id, "کد رفرال نامعتبر است.", reply_markup=get_inline_main_menu())
        conn.close()

# --- ادمین

def admin_panel(message):
    if message.from_user.id not in ADMIN_IDS:
        return

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("افزایش سکه", callback_data="admin_add_coins"),
        types.InlineKeyboardButton("کاهش سکه", callback_data="admin_reduce_coins")
    )
    markup.add(
        types.InlineKeyboardButton("بن کردن کاربر", callback_data="admin_ban_user"),
        types.InlineKeyboardButton("رفع بن", callback_data="admin_unban_user")
    )

    markup.add(
        types.InlineKeyboardButton("ارسال پیام همه‌گانی", callback_data="admin_broadcast"),
        types.InlineKeyboardButton("قطع چت کاربر", callback_data="admin_disconnect_chat")
    )
    markup.add(
        types.InlineKeyboardButton("داشبورد آماری", callback_data="admin_dashboard")
    )
    markup.add(
    types.InlineKeyboardButton("📡 مدیریت کانال‌ها", callback_data="admin_manage_channels")
    )
    bot.send_message(message.chat.id, "به بخش ادمین خوش آمدید. یک گزینه را انتخاب کنید:", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_")and call.message.chat.type == "private")
def admin_callbacks(call):
    if call.data == "admin_dashboard":
        if call.from_user.id not in ADMIN_IDS:
            return
        admin_dashboard(call)
    elif call.data == "admin_add_channel":
        if call.from_user.id not in ADMIN_IDS:
            return
        start_add_channel(call.message) 
    elif call.data == "admin_list_channels":
        if call.from_user.id not in ADMIN_IDS:
            return
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, title, chat_id, expire_at FROM channels")
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return bot.edit_message_text("❗️هیچ کانالی ثبت نشده است.", call.message.chat.id, call.message.message_id)

        for row in rows:
            ch_id, title, chat_id, expire = row
            text = f"📡 {title}\n🆔{chat_id}\n⏰ انقضا: {expire}"
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("❌ حذف", callback_data=f"admin_delete_channel_{ch_id}"))
            bot.send_message(call.message.chat.id, text, reply_markup=markup)

    elif call.data.startswith("admin_delete_channel_"):
        if call.from_user.id not in ADMIN_IDS:
            return
        ch_id = int(call.data.split("_")[-1])
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM channels WHERE id = ?", (ch_id,))
        conn.commit()
        conn.close()
        bot.send_message(call.message.chat.id, "✅ کانال حذف شد.")
        bot.delete_message(call.message.chat.id, call.message.message_id)

    elif call.data == "admin_manage_channels":
        if call.from_user.id not in ADMIN_IDS:
            return
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("➕ افزودن کانال", callback_data="admin_add_channel"),
            types.InlineKeyboardButton("📃 لیست کانال‌ها", callback_data="admin_list_channels")
        )
        bot.edit_message_text("لطفاً یکی از گزینه‌های مدیریت کانال را انتخاب کنید:", call.message.chat.id, call.message.message_id, reply_markup=markup)
    elif call.data == "admin_add_coins":
        if call.from_user.id not in ADMIN_IDS:
            return
        msg = bot.send_message(call.message.chat.id, "شناسه کاربر و مقدار سکه برای افزایش را به این صورت وارد کنید: user_id amount")
        bot.register_next_step_handler(msg, add_coins)
    elif call.data == "admin_reduce_coins":
        if call.from_user.id not in ADMIN_IDS:
            return
        msg = bot.send_message(call.message.chat.id, "شناسه کاربر و مقدار سکه برای کاهش را به این صورت وارد کنید: user_id amount")
        bot.register_next_step_handler(msg, reduce_coins)
    elif call.data == "admin_ban_user":
        if call.from_user.id not in ADMIN_IDS:
            return
        msg = bot.send_message(call.message.chat.id, "شناسه کاربر برای بن کردن را وارد کنید:")
        bot.register_next_step_handler(msg, ban_user)
    elif call.data == "admin_unban_user":
        if call.from_user.id not in ADMIN_IDS:
            return
        msg = bot.send_message(call.message.chat.id, "شناسه کاربر برای رفع بن را وارد کنید:")
        bot.register_next_step_handler(msg, admin_unban_user)
    elif call.data == "admin_disconnect_chat":
        if call.from_user.id not in ADMIN_IDS:
            return
        msg = bot.send_message(call.message.chat.id, "شناسه کاربر مورد نظر برای قطع چت را وارد کنید:")
        bot.register_next_step_handler(msg, admin_disconnect_chat)
    elif call.data == "admin_broadcast":
        if call.from_user.id not in ADMIN_IDS:
            return
        msg = bot.send_message(call.message.chat.id, "پیام برای ارسال به همه کاربران را وارد کنید: - برای لغو ارسال پیام کلمه : 'لغو' را وارد کنید.")
        bot.register_next_step_handler(msg, broadcast_message)
    else:
        bot.send_message(call.message.chat.id, "گزینه نامعتبر!")

admin_inputs = {}

def start_add_channel(message):
    admin_inputs[message.from_user.id] = {}
    msg = bot.send_message(message.chat.id, "مرحله 1️⃣: لطفاً `chat_id` کانال را وارد کنید:", parse_mode="Markdown")
    bot.register_next_step_handler(msg, get_chat_id)

def get_chat_id(message):
    user_id = message.from_user.id
    if user_id not in admin_inputs:
        admin_inputs[user_id] = {}
    
    admin_inputs[user_id]["chat_id"] = message.text.strip()
    msg = bot.reply_to(message, "مرحله 2️⃣: حالا `نام کانال` را وارد کنید:")
    bot.register_next_step_handler(msg, get_title)

def get_title(message):
    title = message.text.strip()
    if not title:
        msg = bot.send_message(message.chat.id, "❌ نام کانال نمی‌تواند خالی باشد. دوباره وارد کنید:")
        bot.register_next_step_handler(msg, get_title)
        return
    admin_inputs[message.from_user.id]["title"] = title
    msg = bot.send_message(message.chat.id, f"مرحله 3️⃣: حالا `لینک دعوت` کانال را وارد کنید:\n http://{LINK}/ ")
    bot.register_next_step_handler(msg, get_link)

def get_link(message):
    try:
        link = message.text.strip()
        
        # if not link.startswith("http"):
        #     error_text = "❌ لینک باید با http یا https شروع شود. لطفاً لینک صحیح وارد کنید:"
        #     msg = bot.send_message(
        #         chat_id=message.chat.id,
        #         text=error_text
        #     )
        #     bot.register_next_step_handler(msg, get_link)
        #     return
        
        admin_inputs[message.from_user.id]["link"] = link
        
        instruction_text = (
            "مرحله 4️⃣: لطفاً *زمان انقضا* را به صورت *HH:MM* وارد کنید:\n"
            "مثال: 23:59\n"
            "00:30\n"
            "9999:00"
        )
        
        msg = bot.send_message(
            chat_id=message.chat.id,
            text=instruction_text
        )
        
        bot.register_next_step_handler(msg, get_expire_date)
    
    except Exception as e:
        print(f"خطا در get_link: {e}")
        bot.reply_to(message, "❌ خطایی در پردازش رخ داد.")

def get_expire_date(message):
    try:
        user_input = message.text.strip()
        
        if user_input.count(":") != 1:
            raise ValueError("فرمت نامعتبر")
        
        hours_str, minutes_str = user_input.split(":")
        hours = int(hours_str)
        minutes = int(minutes_str)
        
        if hours < 0 or minutes < 0:
            raise ValueError("مقادیر منفی مجاز نیستند!")
        
        delta = timedelta(hours=hours, minutes=minutes)
        
        expire_at = datetime.now() + delta
        
        if expire_at.year > 9999:
            raise ValueError("زمان وارد شده بیش از حد بزرگ است!")
        
        data = admin_inputs.pop(message.from_user.id)
        add_channel(
            data["chat_id"],
            data["title"],
            data["link"],
            expire_at.strftime("%Y-%m-%d %H:%M:%S")
        )
        
        bot.send_message(message.chat.id, "✅ کانال با موفقیت ثبت شد.")
    
    except OverflowError:
        msg = bot.send_message(
            message.chat.id,
            "عدد کوچیک تر وارد کن"
        )
        bot.register_next_step_handler(msg, get_expire_date)
    
    except (ValueError, IndexError):
        instruction_text = (
            "مرحله 4️⃣: لطفاً *زمان انقضا* را به صورت *HH:MM* وارد کنید:\n"
            "مثال: 23:59\n"
            "00:30\n"
            "9999:00"
        )
        msg = bot.send_message(
            message.chat.id,
            instruction_text
        )
        bot.register_next_step_handler(msg, get_expire_date)
    
    except Exception as e:
        admin_inputs.pop(message.from_user.id, None)
        bot.send_message(
            message.chat.id,
            f"❌ خطای سیستمی: {str(e)}"
        )


def admin_unban_user(message):
    try:
        user_id = int(message.text.strip())
    except ValueError:
        bot.reply_to(message, "شناسه وارد شده معتبر نیست!")
        return
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM banned_users WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
    bot.reply_to(message, f"کاربر {user_id} از حالت بن خارج شد.")

def admin_dashboard(call):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM active_chats")
        active_chats = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM banned_users")
        banned_users = cursor.fetchone()[0]
        conn.close()

    text = f"""
داشبورد آماری:
--------------------
تعداد کل کاربران: {total_users}
چت‌های فعال: {active_chats}
کاربران بن‌شده: {banned_users}
"""
    bot.edit_message_text(text, call.message.chat.id, call.message.message_id)

def admin_disconnect_chat(message):
    try:
        target_id = int(message.text.strip())
    except ValueError:
        bot.reply_to(message, "شناسه وارد شده معتبر نیست!")
        return

    partner_id = remove_active_chat(target_id)

    if partner_id:
        bot.reply_to(message, f"چت کاربر {target_id} به همراه کاربر {partner_id} قطع شد.")
        bot.send_message(target_id, "چت شما توسط سیستم به صورت خودکار قطع شد.", reply_markup=get_inline_main_menu())
        bot.send_message(partner_id, "چت شما توسط سیستم به صورت خودکار قطع شد.", reply_markup=get_inline_main_menu())
    else:
        bot.reply_to(message, "کاربر مورد نظر در چت فعال نمی‌باشد.")


def process_send_to_all_amount(message):
    try:
        amount = int(message.text)
        if amount <= 0:
            bot.reply_to(message, "❌ مقدار باید بزرگتر از صفر باشد!")
            return

        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM users")
        users = cursor.fetchall()

        success = 0
        failed = 0
        for user in users:
            try:
                cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user[0]))
                success += 1
            except:
                failed += 1

        try:
            bot.send_message(user[0], f"""
        🎉 موجودی حساب شما افزایش یافت!
        • مبلغ: {amount} تومان
        • توضیحات: واریز دسته‌جمعی توسط مدیریت
            """)
        except:
            pass

        conn.commit()
        conn.close()

        bot.reply_to(message, f"""
 عملیات با موفقیت انجام شد!
• تعداد کاربران موفق: {success}
• تعداد کاربران ناموفق: {failed}
• مبلغ اضافه شده: {amount} تومان
        """)

    except ValueError:
        bot.reply_to(message, " لطفا یک عدد معتبر وارد کنید!")

def add_coins(message):
    try:
        user_id, amount = map(int, message.text.split())
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET coin_balance = coin_balance + ? WHERE user_id = ?", (amount, user_id))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, f" {amount} سکه به کاربر {user_id} اضافه شد.")
        bot.send_message(user_id, f"✅ سکه شما به مقدار {amount} افزایش یافت")
    except:
        bot.send_message(message.chat.id, "خطا در فرمت ورودی. لطفاً به‌درستی وارد کنید: user_id amount")

def reduce_coins(message):
    try:
        user_id, amount = map(int, message.text.split())
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET coin_balance = coin_balance - ? WHERE user_id = ? AND coin_balance >= ?", (amount, user_id, amount))
        if cursor.rowcount == 0:
            bot.send_message(message.chat.id, "❌ کاربر سکه کافی برای کاهش ندارد یا شناسه نامعتبر است.")
        else:
            conn.commit()
            bot.send_message(message.chat.id, f" {amount} سکه از کاربر {user_id} کسر شد.")
            bot.send_message(user_id, f"✅ سکه شما به مقدار {amount} کاهش یافت")
        conn.close()
    except:
        bot.send_message(message.chat.id, "خطا در فرمت ورودی. لطفاً به‌درستی وارد کنید: user_id amount")

def ban_user(message):
    user_id = message.text.strip()
    try:
        user_id = int(user_id)
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO banned_users (user_id, ban_reason) VALUES (?, ?)", (user_id, "بن توسط ادمین"))
        conn.commit()
        conn.close()
        bot.reply_to(message, f"کاربر {user_id} با موفقیت بن شد.")
    except ValueError:
        bot.reply_to(message, "شناسه وارد شده معتبر نیست.")

def add_balance(message):
    try:
        user_id, amount = map(int, message.text.split())
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
        conn.commit()
        conn.close()
        bot.reply_to(message, f"موجودی کاربر {user_id} به مقدار {amount} افزایش یافت.")
    except Exception as e:
        bot.reply_to(message, "خطا در افزایش موجودی. لطفاً فرمت ورودی را درست وارد کنید.")

def reduce_balance(message):
    try:
        user_id, amount = map(int, message.text.split())
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (amount, user_id))
        conn.commit()
        conn.close()
        bot.reply_to(message, f"موجودی کاربر {user_id} به مقدار {amount} کاهش یافت.")
    except Exception as e:
        bot.reply_to(message, "خطا در کاهش موجودی. لطفاً فرمت ورودی را درست وارد کنید.")

def broadcast_message(message):

    if message.text == "لغو":
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("افزایش سکه", callback_data="admin_add_coins"),
            types.InlineKeyboardButton("کاهش سکه", callback_data="admin_reduce_coins")
        )
        markup.add(
            types.InlineKeyboardButton("بن کردن کاربر", callback_data="admin_ban_user"),
            types.InlineKeyboardButton("رفع بن", callback_data="admin_unban_user")
        )

        markup.add(
            types.InlineKeyboardButton("ارسال پیام همه‌گانی", callback_data="admin_broadcast"),
            types.InlineKeyboardButton("قطع چت کاربر", callback_data="admin_disconnect_chat")
        )
        markup.add(
            types.InlineKeyboardButton("داشبورد آماری", callback_data="admin_dashboard")
        )
        markup.add(
        types.InlineKeyboardButton("📡 مدیریت کانال‌ها", callback_data="admin_manage_channels")
        )
        bot.send_message(message.chat.id, "به بخش ادمین خوش آمدید. یک گزینه را انتخاب کنید:", reply_markup=markup)

        return

    content_type = message.content_type

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    rows = cursor.fetchall()
    conn.close()

    total_users = len(rows)
    success = 0
    failed = 0
    blocked = 0
    start_time = time.time()

    progress_msg = bot.send_message(
        message.chat.id, 
        f"شروع ارسال پیام...\nکل کاربران: {total_users}\nپردازش شده: 0\nارسال موفق: 0\nارسال ناموفق: 0\nکاربران بلاک شده: 0\nزمان: 0 ثانیه"
    )

    for idx, row in enumerate(rows, start=1):
        user_id = row[0]
        try:
            if content_type == "text":
                bot.send_message(user_id, message.text)
            elif content_type == "photo":
                bot.send_photo(user_id, message.photo[-1].file_id, caption=message.caption if hasattr(message, 'caption') else "")
            elif content_type == "document":
                bot.send_document(user_id, message.document.file_id, caption=message.caption if hasattr(message, 'caption') else "")
            elif content_type == "video":
                bot.send_video(user_id, message.video.file_id, caption=message.caption if hasattr(message, 'caption') else "")
            elif content_type == "audio":
                bot.send_audio(user_id, message.audio.file_id, caption=message.caption if hasattr(message, 'caption') else "")
            elif content_type == "voice":
                bot.send_voice(user_id, message.voice.file_id)
            else:
                if hasattr(message, 'text') and message.text:
                    bot.send_message(user_id, message.text)
                else:
                    bot.send_message(user_id, "پیام مورد نظر قابل ارسال نیست.")
            success += 1
        except Exception as e:
            failed += 1
            if "blocked" in str(e).lower():
                blocked += 1

        time.sleep(random.uniform(0.1, 0.3))  

        if idx % 50 == 0:
            time.sleep(2)

        if idx % 10 == 0 or idx == total_users:
            elapsed = int(time.time() - start_time)
            try:
                bot.edit_message_text(
                    f"در حال ارسال پیام...\nکل کاربران: {total_users}\nپردازش شده: {idx}\nارسال موفق: {success}\nارسال ناموفق: {failed}\nکاربران بلاک شده: {blocked}\nزمان: {elapsed} ثانیه",
                    message.chat.id, progress_msg.message_id
                )
            except Exception:
                pass

    total_time = int(time.time() - start_time)
    bot.reply_to(message, 
        f"ارسال پیام به همه کاربران به پایان رسید.\nکل کاربران: {total_users}\nارسال موفق: {success}\nارسال ناموفق: {failed}\nکاربران بلاک شده: {blocked}\nزمان کل: {total_time} ثانیه")

if __name__ == "__main__":
    print("✅ ربات فعال شد!")
    bot.infinity_polling(timeout=30)
