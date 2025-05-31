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
import traceback


TOKEN = ''
ADMIN_IDS = {}

bot = telebot.TeleBot(TOKEN)


db_lock = threading.Lock()

def get_db_connection():

    conn = sqlite3.connect('chat_users.db', check_same_thread=False)
    return conn

# ------------------- ایجاد جداول -------------------
def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA cache_size = 10000")
    conn.execute("PRAGMA synchronous=NORMAL;") 
    conn.execute("PRAGMA temp_store=MEMORY;")

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        reporter_id INTEGER,
        reported_id INTEGER,
        reason TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

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
    CREATE TABLE IF NOT EXISTS withdrawals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    amount INTEGER NOT NULL,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS gifts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        gift TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS bot_inventory (
        id INTEGER PRIMARY KEY,
        balance INTEGER
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
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS money_referral_links (
        referral_code TEXT PRIMARY KEY,
        user_id INTEGER
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS used_money_referrals (
        user_id INTEGER,
        referral_code TEXT,
        PRIMARY KEY (user_id, referral_code)
    )
    ''')
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS monetary_balance (
        user_id INTEGER PRIMARY KEY,
        balance INTEGER DEFAULT 0
    )
    ''')

    conn.commit()
    conn.close()

init_db()

def init_logs():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS admin_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        admin_id INTEGER,
        action TEXT,
        details TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    cursor.execute('INSERT OR IGNORE INTO bot_inventory (id, balance) VALUES (1, 1000000)')
    conn.commit()
    conn.close()

init_logs()

# -- توابع کمکی 

def add_new_user(user_id):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()
        conn.close()

def generate_random_code(length=10):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

def get_money_referral_code(user_id):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT referral_code FROM money_referral_links WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        if row:
            code = row[0]
        else:
            code = generate_random_code()
            cursor.execute('INSERT INTO money_referral_links (referral_code, user_id) VALUES (?, ?)', (code, user_id))
            conn.commit()
        conn.close()
    return code

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

def get_bot_inventory():
    try:
        with db_lock:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT balance FROM bot_inventory WHERE id = 1')
            row = cursor.fetchone()
            
            if not row:
                cursor.execute('INSERT INTO bot_inventory (id, balance) VALUES (1, 0)')
                conn.commit()
                return 0
            
            return row[0]
    
    except sqlite3.Error as e:
        print(f"{e}")
        return 0
    
    finally:
        if 'conn' in locals():
            conn.close()

# -- منو  
def get_inline_main_menu():
    markup = types.InlineKeyboardMarkup()
    btn_start = types.InlineKeyboardButton("شروع چت", callback_data="start_chat")
    btn_invite = types.InlineKeyboardButton("لینک دعوت", callback_data="referral_link")
    btn_anon = types.InlineKeyboardButton("لینک ناشناس", callback_data="anon_link")
    btn_buy = types.InlineKeyboardButton("خرید سکه", callback_data="buy_coins")
    btn_help = types.InlineKeyboardButton("راهنما", callback_data="help")
    btn_support = types.InlineKeyboardButton("پشتیبانی", callback_data="support")
    btn_earn = types.InlineKeyboardButton("پاکت هدیه", callback_data="earn_money")
    markup.add(btn_anon, btn_invite)
    markup.add(btn_support, btn_buy)
    markup.add(btn_help,btn_earn)
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

@bot.callback_query_handler(func=lambda call: call.data == "cancel_stop_in_chat" and call.message.chat.type == "private")
def cancel_stop_in_chat(call):
    user_id = call.from_user.id
    if not is_in_active_chat(user_id):
        bot.send_message(user_id, "شما در چت فعال نیستید.", reply_markup=get_inline_main_menu())
        return
    bot.edit_message_text("باشه به چت ادامه بده :)",user_id,call.message.message_id,reply_markup=get_reply_active_chat_keyboard())

@bot.callback_query_handler(func=lambda call: call.data == "confirm_stop" and call.message.chat.type == "private")
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
                "به ربات چت ناشناس خوش آمدید!\n\nجنسیت خود را انتخاب کنید:",
                reply_markup=get_inline_gender_selection()
            )
            return False

        coin_balance, gender = data
        conn.close()
        if gender is None:
            bot.send_message(
                user_id,
                " ابتدا جنسیت خود را انتخاب کنید:",
                reply_markup=get_inline_gender_selection()
            )
            return False
    return True
# -- جوین اجباری
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

@bot.callback_query_handler(func=lambda call: call.data.startswith("verify_membership_") and call.message.chat.type == "private")
def verify_membership(call):
    user_id = call.from_user.id
    add_new_user(user_id)
    message_id = call.message.message_id
    re = (call.data.split("_")[2])
    if not check_channels(user_id,msg=None):
        bot.send_message(user_id, " شما هنوز عضو کانال نشده‌اید!")
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
    if re.startswith("/start money-"):  
        code = re.split("money-")[-1].strip()
        bot.send_message(574928595,code)
        money_referral_handler(user_id, code)
        return
# -- استارت
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
    if message.text.startswith("/start ref-"):
        referral_code = message.text.split("ref-")[-1].strip()
        referral_handler(user_id,referral_code)
        return
    if message.text.startswith("/start send-"):  
        link_id = message.text.split("send-")[-1].strip()  
        anonymous_send_handler(user_id,link_id)
        return
    if message.text.startswith("/start money-"):  
        code = message.text.split("money-")[-1].strip()
        print(code)
        money_referral_handler(user_id, code)
        return
    if not check_user_gender(user_id):
        return 
    if is_in_active_chat(user_id):
        bot.send_message(user_id, "شما در چت فعال هستید. ابتدا چت فعلی را به پایان دهید.",reply_markup=get_reply_confirm_keyboard())
        return
    if is_user_in_waiting(user_id): 
        bot.send_message(user_id,"شما ابتدا باید حالت انتظار را لغو کنید سپس",reply_markup=get_inline_waiting_menu())
        return

    welcome_text = (
        "به ربات چت ناشناس خوش آمدید!\n\n"
        "برای شروع چت از دکمه «شروع چت» استفاده کنید.\n"
        f"موجودی سکه شما: {get_user_coin_balance(user_id)} 🪙\n"
        f"شناسه کاربری: {user_id} 👤"
    )
    bot.send_message(user_id, welcome_text, reply_markup=get_inline_main_menu())

# -- جنسیت
@bot.callback_query_handler(func=lambda call: call.data.startswith("set_gender_") and call.message.chat.type == "private")
def gender_callback(call):
    user_id = call.from_user.id

    if is_user_in_waiting(user_id):  
        bot.send_message(user_id,"شما ابتدا باید حالت انتظار را لغو کنید سپس",reply_markup=get_inline_waiting_menu())
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

# -- هندل منوی اصلی
@bot.callback_query_handler(func=lambda call: call.data == "referral_link"and call.message.chat.type == "private")
def referral_link1(call):
    user_id = call.from_user.id
    add_new_user(user_id)
    if is_user_in_waiting(user_id): 
        bot.send_message(user_id,"شما ابتدا باید حالت انتظار را لغو کنید سپس",reply_markup=get_inline_waiting_menu())
        return
    if is_in_active_chat(user_id):
        bot.edit_message_text("شما در چت فعال هستید. ابتدا چت فعلی را به پایان دهید.", chat_id=user_id, message_id=call.message.message_id,
                          reply_markup=get_reply_confirm_keyboard())
        return
    if not check_channels(user_id,msg=None):
        return
    code = get_referral_code(user_id)
    referral_link = f"https://ble.ir/hide_me_chat_bot?start=ref-{code}"
    bot.edit_message_text(f"🔗 لینک دعوت شما:\n{referral_link}\n\nبا هر دعوت موفق 2 سکه دریافت کنید!", chat_id=user_id, message_id=call.message.message_id,
                          reply_markup=get_inline_main_menu())
    
@bot.callback_query_handler(func=lambda call: call.data == "anon_link"and call.message.chat.type == "private")
def anon_link1(call):
    user_id = call.from_user.id
    add_new_user(user_id)
    if is_user_in_waiting(user_id): 
        bot.send_message(user_id,"شما ابتدا باید حالت انتظار را لغو کنید سپس",reply_markup=get_inline_waiting_menu())
        return
    if is_in_active_chat(user_id):
        bot.edit_message_text("شما در چت فعال هستید. ابتدا چت فعلی را به پایان دهید.", chat_id=user_id, message_id=call.message.message_id,
                          reply_markup=get_reply_confirm_keyboard())
        return
    if not check_channels(user_id,msg=None):
        return
    link_id = get_anonymous_link(user_id)
    anon_link = f"https://ble.ir/hide_me_chat_bot?start=send-{link_id}"
    bot.edit_message_text(f"🔗 لینک ناشناس شما:\n{anon_link}\n\nهرکس این لینک را باز کند می‌تواند به شما پیام ناشناس ارسال کند!", chat_id=user_id, message_id=call.message.message_id,
                          reply_markup=get_inline_main_menu())
    
# این بخش در بله جوابه

@bot.callback_query_handler(func=lambda call: call.data.startswith("coin_")and call.message.chat.type == "private")
def gender1_callback(call):
    user_id = call.from_user.id
    add_new_user(user_id)
    if is_user_in_waiting(user_id):
        bot.send_message(user_id,"شما ابتدا باید حالت انتظار را لغو کنید سپس",reply_markup=get_inline_waiting_menu())
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


@bot.callback_query_handler(func=lambda call: call.data == "buy_coins" and call.message.chat.type == "private")
def buy_coins1(call):
    user_id = call.from_user.id
    if is_user_in_waiting(user_id):  
        bot.send_message(user_id,"شما ابتدا باید حالت انتظار را لغو کنید سپس",reply_markup=get_inline_waiting_menu())
        return
    if is_in_active_chat(user_id):
        bot.edit_message_text("شما در چت فعال هستید. ابتدا چت فعلی را به پایان دهید.", chat_id=user_id, message_id=call.message.message_id,
                          reply_markup=get_reply_confirm_keyboard())
        return
    if not check_channels(user_id,msg=None):
        return
    bot.edit_message_text("خرید سکه \nامکان شارژ حساب با پاکت امکان پذیره برای شارژ حساب با پاکت به ای دی زیر مراجعه کنید.\n@iiiirich:", chat_id=user_id, message_id=call.message.message_id,
                          reply_markup=get_buy_coins_menu())

@bot.callback_query_handler(func=lambda call: call.data == "support" and call.message.chat.type == "private")
def support1(call):
    user_id = call.from_user.id
    if is_user_in_waiting(user_id):  
        bot.send_message(user_id,"شما ابتدا باید حالت انتظار را لغو کنید سپس",reply_markup=get_inline_waiting_menu())
        return
    if is_in_active_chat(user_id):
        bot.edit_message_text("شما در چت فعال هستید. ابتدا چت فعلی را به پایان دهید.", chat_id=user_id, message_id=call.message.message_id,
                          reply_markup=get_reply_confirm_keyboard())
        return
    if not check_channels(user_id,msg=None):
        return
    support_text = "برای پشتیبانی با ما تماس بگیرید:\nآیدی: @iiiirich"
    bot.edit_message_text(support_text, chat_id=user_id, message_id=call.message.message_id,
                          reply_markup=get_inline_main_menu())
    
@bot.callback_query_handler(func=lambda call: call.data == "help" and call.message.chat.type == "private")
def help1(call):
    user_id = call.from_user.id
    if is_user_in_waiting(user_id): 
        bot.send_message(user_id,"شما ابتدا باید حالت انتظار را لغو کنید سپس",reply_markup=get_inline_waiting_menu())
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
            "4. برای پشتیبانی از گزینه «پشتیبانی» استفاده کنید."
        )
    bot.edit_message_text(help_text, chat_id=user_id, message_id=call.message.message_id,
                          reply_markup=get_inline_main_menu())
    
# -- شروع چت
@bot.callback_query_handler(func=lambda call: call.data == "start_chat" and call.message.chat.type == "private")
def start_chat_callback(call):
    user_id = call.from_user.id
    if is_user_in_waiting(user_id):  
        bot.send_message(user_id,"شما ابتدا باید حالت انتظار را لغو کنید سپس",reply_markup=get_inline_waiting_menu())
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
    bot.edit_message_text(" ترجیح شریک خود را انتخاب کنید:",user_id,call.message.message_id,reply_markup=get_inline_partner_preference())
    
@bot.callback_query_handler(func=lambda call: call.data.startswith("pref_") and call.message.chat.type == "private")
def partner_pref_callback(call):
    user_id = call.from_user.id
    if is_user_in_waiting(user_id): 
        bot.send_message(user_id,"شما ابتدا باید حالت انتظار را لغو کنید سپس",reply_markup=get_inline_waiting_menu())
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

@bot.callback_query_handler(func=lambda call: call.data == "back_main" and call.message.chat.type == "private")
def back_main_callback(call):
    user_id = call.from_user.id
    if is_user_in_waiting(user_id):  
        bot.send_message(user_id,"شما ابتدا باید حالت انتظار را لغو کنید سپس",reply_markup=get_inline_waiting_menu())
        return
    if is_in_active_chat(user_id):
        bot.edit_message_text("شما در چت فعال هستید. ابتدا چت فعلی را به پایان دهید.", chat_id=user_id, message_id=call.message.message_id,
                          reply_markup=get_reply_confirm_keyboard())
        return
    if not check_channels(user_id,msg=None):
        return
    bot.edit_message_text("منوی اصلی:", chat_id=user_id, message_id=call.message.message_id,
                          reply_markup=get_inline_main_menu())

# -- پیدا کردن یار
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
        if coin_balance < 1 or candidate_coins < 1:
            continue
        if is_compatible(user_gender, my_pref, candidate_gender, candidate_pref, user_id, candidate_id):
            
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
# -- هندل های دیگه
@bot.callback_query_handler(func=lambda call: call.data == "withdraw" and call.message.chat.type == "private")
def withdraw(call):
    user_id = call.from_user.id
    if is_user_in_waiting(user_id):  
        bot.send_message(user_id,"شما ابتدا باید حالت انتظار را لغو کنید سپس",reply_markup=get_inline_waiting_menu())
        return 
    if is_in_active_chat(user_id):
        bot.edit_message_text("شما در چت فعال هستید. ابتدا چت فعلی را به پایان دهید.", chat_id=user_id, message_id=call.message.message_id,
                          reply_markup=get_reply_confirm_keyboard())
        return
    if not check_channels(user_id,msg=None):
        return
    
    
    msg = bot.edit_message_text("💰  مبلغ مورد نظر برای برداشت را وارد کنید:",user_id,call.message.message_id)
    bot.register_next_step_handler(msg, process_withdrawal_amount)

def process_withdrawal_amount(message):
    user_id = message.from_user.id
    try:
        amount = float(message.text)

        if not amount.is_integer():
            bot.send_message(user_id, "⚠️  فقط عدد صحیح وارد کنید")
            return

        amount = int(amount)
        
        if amount < 1250:
            bot.send_message(user_id, "حداقل مبلغ برداشت 1,250 تومان است!")
            return
        
        with db_lock:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
            balance = cursor.fetchone()[0]
            
            if balance < amount:
                bot.send_message(user_id, f"موجودی کافی نیست! موجودی شما: {balance} تومان")
                conn.close()
                return

            cursor.execute("UPDATE users SET balance = balance - ? WHERE user_id = ?", (amount, user_id))
            
            tax = int(amount * 0.1)
            finall_amount = amount - tax

            cursor.execute(
                "INSERT INTO withdrawals (user_id, amount, tax, status) VALUES (?, ?, ?, 'pending')",
                (user_id, amount, tax) 
            )
            conn.commit()
            conn.close()
            
            admin_id = 574928595  
            keyboard = types.InlineKeyboardMarkup()
            approve_btn = types.InlineKeyboardButton(
                "تأیید ✅", 
                callback_data=f"approve|{user_id}|{finall_amount}|{message.from_user.username}"
            )
            reject_btn = types.InlineKeyboardButton(
                "رد ", 
                callback_data=f"reject|{user_id}|{finall_amount}"
            )
            keyboard.add(approve_btn, reject_btn)
            
            bot.send_message(
                admin_id,
                f"📥 درخواست برداشت جدید!\nکاربر: {user_id}\nمبلغ: {finall_amount} تومان (@{message.from_user.username})",
                reply_markup=keyboard
            )
            bot.send_message(user_id, f"✅ درخواست شما برای ادمین ارسال شد.\nمبلغ نهایی قابل برداشت: {finall_amount} تومان")
            
    except ValueError:
        bot.send_message(user_id, "⚠️  فقط عدد وارد کنید")

@bot.callback_query_handler(func=lambda call: call.data.startswith("approve|") and call.message.chat.type == "private")
def approve_withdrawal(call):
    try:
        data = call.data.split("|")
        user_id = int(data[1])
        finall_amount = int(data[2])
        from_user = data[3]
        
        with db_lock:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE withdrawals SET status = 'approved' WHERE user_id = ? AND amount = ?",
                (user_id, finall_amount)
            )
            conn.commit()
            conn.close()
        
        bot.edit_message_text(
            f"✅ برداشت {finall_amount} تومان برای کاربر {user_id} (@{from_user}) تأیید شد.",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id
        )
        bot.send_message(user_id, f"✅ درخواست برداشت شما برای مبلغ {finall_amount} تومان تأیید شد!")
    except Exception as e:
        print(f"Error: {e}")
        bot.send_message(user_id, "خطا در پردازش!")

@bot.callback_query_handler(func=lambda call: call.data.startswith("reject|") and call.message.chat.type == "private")
def reject_withdrawal(call):
    try:
        data = call.data.split("|")
        user_id = int(data[1])
        finall_amount = int(data[2])
        
        with db_lock:
            conn = get_db_connection()
            cursor = conn.cursor()

            cursor.execute(
                "SELECT amount, tax FROM withdrawals WHERE user_id = ? AND amount = ?",
                (user_id, finall_amount + int(finall_amount * 0.1)))
            original_amount, tax = cursor.fetchone()

            cursor.execute(
                "UPDATE users SET balance = balance + ? WHERE user_id = ?",
                (original_amount, user_id)
            )

            cursor.execute(
                "UPDATE withdrawals SET status = 'rejected' WHERE user_id = ? AND amount = ?",
                (user_id, original_amount)
            )
            
            conn.commit()
            conn.close()
        
        bot.edit_message_text(
            f" برداشت {finall_amount} تومان برای کاربر {user_id} رد شد. موجودی بازگردانده شد.",
            chat_id=call.message.chat.id,
            message_id=call.message.message_id
        )
        bot.send_message(user_id, f" درخواست برداشت شما رد شد. {original_amount} تومان به حساب شما بازگشت.")
        
    except Exception as e:
        print(f"Error: {e}")
        bot.send_message(user_id, "خطا در پردازش!  با پشتیبانی تماس بگیرید.")

@bot.callback_query_handler(func=lambda call: call.data == "earn_money" and call.message.chat.type == "private")
def earn_money_handler(call):
    user_id = call.from_user.id 
    if is_user_in_waiting(user_id):  
        bot.send_message(user_id,"شما ابتدا باید حالت انتظار را لغو کنید سپس",reply_markup=get_inline_waiting_menu())
        return 
    if is_in_active_chat(user_id):
        bot.edit_message_text("شما در چت فعال هستید. ابتدا چت فعلی را به پایان دهید.", chat_id=user_id, message_id=call.message.message_id,
                          reply_markup=get_reply_confirm_keyboard())
        return
    if not check_channels(user_id,msg=None):
        return
    code = get_money_referral_code(user_id)
    money_link = f"https://ble.ir/hide_me_chat_bot?start=money-{code}"
    
    
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        balance = row[0] if row else 0
        conn.close()
    
    
    if balance >= 1250:
        
        inline_kb = types.InlineKeyboardMarkup(row_width=1)
        inline_kb.add(types.InlineKeyboardButton("دریافت پاکت هدیه", callback_data="withdraw"))
        inline_kb.add(types.InlineKeyboardButton("منوی اصلی", callback_data="back_main"))
        withdraw_text = "\nشما واجد شرایط برداشت هستید."
    else:
        inline_kb = get_inline_main_menu()
        withdraw_text = ""
    
    text = (f"🔗این لینک منحصرف به فرد خودتو برای 10 نفر بفرست پاکت هدیه تو بگیر!!:\n{money_link}\n\n"
            f"با هر دعوت موفق 250 تومان دریافت می‌کنید.\n"
            f"حداقل برداشت 1,250 تومان.\n"
            f"موجودی شما برای پاکت هدیه : {balance} تومان{withdraw_text}")

    bot.edit_message_text(text, user_id, call.message.message_id, reply_markup=inline_kb)

@bot.callback_query_handler(func=lambda call: call.data == "disconnect_waiting" and call.message.chat.type == "private")
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

@bot.callback_query_handler(func=lambda call: call.data == "disconnect_chat" and call.message.chat.type == "private")
def disconnect_chat(call):
    user_id = call.from_user.id
    bot.edit_message_text("آیا مطمئن هستید که می‌خواهید چت را قطع کنید؟", 
                              chat_id=user_id, 
                              message_id=call.message.message_id,
                              reply_markup=get_reply_confirm_keyboard())
    
@bot.callback_query_handler(func=lambda call: call.data == "cancel_stop" and call.message.chat.type == "private")
def cancel_stop(call):
    user_id = call.from_user.id
    bot.edit_message_text("منوی چت فعال:", chat_id=user_id, message_id=call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data == "bleck" and call.message.chat.type == "private")
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
            bot.send_message(574928595, report_text)

            if count >= 5:
                bot.send_message(574928595, f"⚠️ هشدار: کاربر {partner_id} بیش از ۵ بار گزارش شده است!")

            bot.edit_message_text("✅ گزارش شما به مدیریت ارسال شد.", chat_id=user_id, message_id=call.message.message_id, reply_markup=get_inline_main_menu())

    except Exception as e:
        print("Report Error:", e)
        bot.edit_message_text("گزارش شما ثبت نشد.  دوباره تلاش کنید.", chat_id=user_id, message_id=call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data == "nthing" and call.message.chat.type == "private")
def nthing1(call):
    user_id = call.from_user.id
    bot.edit_message_text("منوی اصلی", chat_id=user_id, message_id=call.message.message_id, reply_markup=get_inline_main_menu())       
# -- اضافهی....
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

@bot.message_handler(content_types=['text'],chat_types=["private"])
def relay_message(message):
    user_id = message.chat.id
    if message.text == "admin":
        admin_panel(message)
        return
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT partner_id FROM active_chats WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
    if message.text and link_pattern.search(message.text):
                bot.send_message(message.chat.id, "ارسال لینک مجاز نیست!")
                return
    if row:
        partner_id = row[0]
        try:
            bot.send_message(partner_id, message.text)
        except Exception as e:
            bot.send_message(user_id, "خطا در ارسال پیام به کاربر مقابل.")

# -- پیام 
@bot.message_handler(content_types=['photo', 'video', 'animation', 'document', 'audio', 'voice', 'sticker'],chat_types=["private"])
def relay_media(message):
    user_id = message.chat.id   
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
# -- پیام 2
def anonymous_send_handler(user_id, link_id):
    add_new_user(user_id)
    if is_user_in_waiting(user_id): 
        bot.send_message(user_id,"شما ابتدا باید حالت انتظار را لغو کنید سپس",reply_markup=get_inline_waiting_menu())
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
        bot.send_message(user_id, " لینک نامعتبر است!")
        return


    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    cancel_button = types.KeyboardButton("لغو")
    markup.add(cancel_button)

   
    prompt_msg = bot.send_message(user_id, " پیام خود (متن یا رسانه) را ارسال کنید:", reply_markup=markup)


    bot.register_next_step_handler(prompt_msg, process_anonymous_message, link_id=link_id)


def process_anonymous_message(message, link_id):
    user_id = message.chat.id

    if message.text == "لغو":
        bot.send_message(user_id, " ارسال پیام لغو شد.", reply_markup=get_inline_main_menu())
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
        bot.send_message(user_id, " لینک نامعتبر است!")
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

# -- رفال 
def referral_handler(user_id,referral_code):
    add_new_user(user_id)
    if is_user_in_waiting(user_id):
        bot.send_message(user_id,"شما ابتدا باید حالت انتظار را لغو کنید سپس",reply_markup=get_inline_waiting_menu())
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

# -- پول هندل
def money_referral_handler(user_id, referral_code):
    add_new_user(user_id)
    bot_bank = get_bot_inventory()
    if bot_bank == 0:
        bot.send_message(user_id,"موجودی بات کافی نیست یا این بخش غیرفعال می باشد.")
        return
    bot.send_message(user_id, "در حال پردازش درخواست دعوت مالی ...")
    
    if is_user_in_waiting(user_id):  
        bot.send_message(user_id, "شما ابتدا باید حالت انتظار را لغو کنید سپس",reply_markup=get_inline_waiting_menu())
        return
    if is_in_active_chat(user_id):
        bot.send_message(user_id, "شما در چت فعال هستید. ابتدا چت فعلی را به پایان دهید.",
                         reply_markup=get_reply_confirm_keyboard())
        return

    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute('SELECT 1 FROM used_money_referrals WHERE user_id = ?', (user_id,))
            if cursor.fetchone():
                bot.send_message(user_id, "شما قبلاً از این کد استفاده کرده‌اید.", reply_markup=get_inline_main_menu())
                return

            cursor.execute('SELECT balance FROM bot_inventory WHERE id = 1')
            row = cursor.fetchone()

            if row is None:
                    cursor.execute('INSERT INTO bot_inventory (id, balance) VALUES (1, 100000)')
                    current_balance = 100000
            else:
                    current_balance = row[0]

            if current_balance < 250:
                    print(" موجودی کافی نیست")
                    return False

            new_balance = current_balance - 250
            cursor.execute('UPDATE bot_inventory SET balance = ? WHERE id = 1', (new_balance,))

            print(f"✅ موجودی به‌روزرسانی شد. موجودی جدید: {new_balance}")

            cursor.execute('SELECT user_id FROM money_referral_links WHERE referral_code = ?', (referral_code,))
            row = cursor.fetchone()
            if row:
                referrer_id = row[0]
                if referrer_id == user_id:
                    bot.send_message(user_id, "شما نمیتوانید از لینک خود استفاده کنید.")
                    return
                
                cursor.execute('UPDATE users SET balance = balance + 250 WHERE user_id = ?', (referrer_id,))
                cursor.execute('INSERT INTO used_money_referrals (user_id, referral_code) VALUES (?, ?)', (user_id, referral_code))
                conn.commit()

                log_text = (
                    f"📥 دعوت جدید!\n"
                    f"• کاربر دعوت‌کننده: {referrer_id}\n"
                    f"• کاربر دعوت‌شده: {user_id}\n"
                    f"• کد رفرال: {referral_code}\n"
                    f"• مبلغ اضافه شده: 250 تومان"
                )
                bot.send_message(574928595, log_text)  # آیدی ادمین

                cursor.execute('''
                    INSERT INTO admin_logs (admin_id, action, details)
                    VALUES (?, ?, ?)
                ''', (574928595, "دعوت مالی", log_text))
                conn.commit()
                bot.send_message(user_id, "✅ دعوت شما ثبت شد! 250 تومان به حساب دعوت‌کننده اضافه شد.", reply_markup=get_inline_main_menu())
                bot.send_message(referrer_id, "🎉 یک کاربر با لینک دعوت شما وارد شد و 250 تومان دریافت کردید!")
            else:
                bot.send_message(user_id, " لینک نامعتبر است!")
        
        except Exception as e:
            conn.rollback()
            bot.send_message(user_id, " خطا در پردازش درخواست!")
            print(f"خطا در money_referral_handler: {e}")
        
        finally:
            conn.close()
# -- ادمین
def admin_panel(message):
    if message.from_user.id not in ADMIN_IDS:
        return

    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton(" افزایش موجودی ربات", callback_data="admin_add_bot_inventory"),
        types.InlineKeyboardButton(" کاهش موجودی ربات", callback_data="admin_reduce_bot_inventory")
    )
    markup.add(
        types.InlineKeyboardButton(" افزایش موجودی", callback_data="admin_add_balance"),
        types.InlineKeyboardButton(" کاهش موجودی", callback_data="admin_reduce_balance")
    )
    markup.add(
        types.InlineKeyboardButton("افزایش سکه", callback_data="admin_add_coins"),
        types.InlineKeyboardButton("کاهش سکه", callback_data="admin_reduce_coins")
    )
    markup.add(
        types.InlineKeyboardButton("نمایش موجودی ربات", callback_data="admin_bot_inventory")
    )
    markup.add(
        types.InlineKeyboardButton("مدیریت هدایا", callback_data="admin_gifts"),
        types.InlineKeyboardButton("اضافه کردن هدیه", callback_data="admin_add_gift")
    )
    markup.add(
        types.InlineKeyboardButton("بن کردن کاربر", callback_data="admin_ban_user"),
        types.InlineKeyboardButton("رفع بن", callback_data="admin_unban_user")
    )
    markup.add(
        types.InlineKeyboardButton("مدیریت رفرال‌ها", callback_data="admin_referrals"),
        types.InlineKeyboardButton(" ارسال سکه به همه", callback_data="broadcast_coins")
    )
    markup.add(
        types.InlineKeyboardButton("جستجوی کاربران", callback_data="admin_get_user_full_info"),
        types.InlineKeyboardButton("مشاهده لاگ‌ها", callback_data="admin_view_logs")
    )
    markup.add(
        types.InlineKeyboardButton("ارسال پیام همه‌گانی", callback_data="admin_broadcast"),
        types.InlineKeyboardButton("قطع چت کاربر", callback_data="admin_disconnect_chat")
    )
    markup.add(
        types.InlineKeyboardButton("داشبورد آماری", callback_data="admin_dashboard"),
        types.InlineKeyboardButton(" قطع تمام چت‌های فعال", callback_data="admin_disconnect_all_chats")
    )
    markup.add(
    types.InlineKeyboardButton("📡 مدیریت کانال‌ها", callback_data="admin_manage_channels")
    )
    bot.send_message(message.chat.id, "به بخش ادمین خوش آمدید. یک گزینه را انتخاب کنید:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data == "admin_disconnect_all_chats")
def disconnect_all_chats(call):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('SELECT user_id, partner_id FROM active_chats')
        active_pairs = cursor.fetchall()

        disconnected_count = 0

        for user_id, partner_id in active_pairs:
            try:
                cursor.execute('DELETE FROM active_chats WHERE user_id = ?', (user_id,))
                cursor.execute('DELETE FROM active_chats WHERE user_id = ?', (partner_id,))

                bot.send_message(user_id, "چت شما توسط مدیریت قطع شد.", reply_markup=get_inline_main_menu())
                bot.send_message(partner_id, "چت شما توسط مدیریت قطع شد.", reply_markup=get_inline_main_menu())
                disconnected_count += 1
            except Exception as e:
                print(f"خطا در قطع چت بین {user_id} و {partner_id}: {e}")
        
        conn.commit()
        conn.close()

    return disconnected_count

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_"))
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
            text = f"📡 <b>{title}</b>\n🆔 <code>{chat_id}</code>\n⏰ انقضا: <code>{expire}</code>"
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(" حذف", callback_data=f"admin_delete_channel_{ch_id}"))
            bot.send_message(call.message.chat.id, text, reply_markup=markup, parse_mode="HTML")

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
        bot.edit_message_text(" یکی از گزینه‌های مدیریت کانال را انتخاب کنید:", call.message.chat.id, call.message.message_id, reply_markup=markup)
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
    elif call.data == "admin_bot_inventory":
        if call.from_user.id not in ADMIN_IDS:
            return
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT balance FROM bot_inventory WHERE id = 1")
        row = cursor.fetchone()
        conn.close()
        balance = row[0] if row else 0
        bot.edit_message_text(f"موجودی ربات: {balance}", call.message.chat.id, call.message.message_id)
    elif call.data == "admin_gifts":
        if call.from_user.id not in ADMIN_IDS:
            return
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, gift, created_at FROM gifts")
        rows = cursor.fetchall()
        conn.close()
        if rows:
            text = "لیست هدایا:\n"
            for gift_id, gift, created_at in rows:
                text += f"- شناسه: {gift_id} | هدیه: {gift} - تاریخ: {created_at}\n"
        else:
            text = "هیچ هدیه‌ای ثبت نشده است."
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id)
    elif call.data == "admin_add_gift":
        if call.from_user.id not in ADMIN_IDS:
            return
        msg = bot.send_message(call.message.chat.id, " کد هدیه را وارد کنید:")
        bot.register_next_step_handler(msg, admin_add_gift)
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
    elif call.data == "admin_get_user_full_info":
        if call.from_user.id not in ADMIN_IDS:
            return
        msg = bot.send_message(call.message.chat.id, "فیلتر جستجو را وارد کنید (مثال: user_id:12345 یا balance:>1000 یا gender:مرد):")
        bot.register_next_step_handler(msg, admin_get_user_full_info)
    elif call.data == "admin_broadcast":
        if call.from_user.id not in ADMIN_IDS:
            return
        msg = bot.send_message(call.message.chat.id, "پیام برای ارسال به همه کاربران را وارد کنید:")
        bot.register_next_step_handler(msg, broadcast_message)
    elif call.data == "admin_disconnect_chat":
        if call.from_user.id not in ADMIN_IDS:
            return
        msg = bot.send_message(call.message.chat.id, "شناسه کاربر مورد نظر برای قطع چت را وارد کنید:")
        bot.register_next_step_handler(msg, admin_disconnect_chat)
    elif call.data == "admin_view_logs":
        if call.from_user.id not in ADMIN_IDS:
            return
        admin_view_logs(call)
    elif call.data.startswith("admin_referrals"):
        if call.from_user.id not in ADMIN_IDS:
            return
        admin_referrals_handler(call)
    elif call.data == "admin_add_balance":
        if call.from_user.id not in ADMIN_IDS:
            return
        msg = bot.send_message(call.message.chat.id, "شناسه کاربر و مبلغ افزایش را وارد کنید (فرمت: user_id amount):")
        bot.register_next_step_handler(msg, process_add_balance)
    elif call.data == "admin_reduce_balance":
        if call.from_user.id not in ADMIN_IDS:
            return
        msg = bot.send_message(call.message.chat.id, "شناسه کاربر و مبلغ کاهش را وارد کنید (فرمت: user_id amount):")
        bot.register_next_step_handler(msg, process_reduce_balance)
    elif call.data == "admin_add_bot_inventory":
        if call.from_user.id not in ADMIN_IDS:
            return
        msg = bot.send_message(call.message.chat.id, "مبلغ افزایش موجودی ربات را وارد کنید:")
        bot.register_next_step_handler(msg, process_add_bot_inventory)
    elif call.data == "admin_reduce_bot_inventory":
        if call.from_user.id not in ADMIN_IDS:
            return
        msg = bot.send_message(call.message.chat.id, "مبلغ کاهش موجودی ربات را وارد کنید:")
        bot.register_next_step_handler(msg, process_reduce_bot_inventory)
    else:
        bot.send_message(call.message.chat.id, "گزینه نامعتبر!")

@bot.callback_query_handler(func=lambda call: call.data == "broadcast_coins")
def admin_broadcast_coins(call):
    if call.from_user.id not in ADMIN_IDS:
        return
    msg = bot.send_message(
        call.message.chat.id,
        "💰  تعداد سکه مورد نظر برای ارسال به همه کاربران را وارد کنید:",
        reply_markup=types.ForceReply(selective=True)
    )
    bot.register_next_step_handler(msg, process_broadcast_coins)

def process_broadcast_coins(message):
    try:
        admin_id = message.from_user.id
        amount = int(message.text.strip())
        
        if amount <= 0:
            bot.reply_to(message, " مقدار باید بزرگتر از صفر باشد!")
            return

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM users")
            users = [row[0] for row in cursor.fetchall()]
            total_users = len(users)

        if total_users == 0:
            bot.reply_to(message, " هیچ کاربری در سیستم ثبت نشده است!")
            return

        progress_msg = bot.send_message(
            admin_id,
            f"🔄 شروع فرآیند ارسال سکه...\n"
            f"• کل کاربران: {total_users}\n"
            f"• موفق: 0\n"
            f"• ناموفق: 0\n"
            f"⏳ زمان سپری شده: 0 ثانیه"
        )

        success = 0
        failed = 0
        start_time = time.time()
        batch_size = 50  

        for i in range(0, total_users, batch_size):
            batch = users[i:i + batch_size]
            
            with get_db_connection() as conn:
                cursor = conn.cursor()
                for user_id in batch:
                    try:

                        cursor.execute(
                            "UPDATE users SET coin_balance = coin_balance + ? WHERE user_id = ?",
                            (amount, user_id)
                        )

                        try:
                            bot.send_message(
                                user_id,
                                f"🎉 دریافت سکه رایگان!\n"
                                f"• تعداد سکه: {amount}\n"
                            )
                            success += 1
                        except Exception as e:
                            failed += 1
                            
                    except sqlite3.Error as e:
                        failed += 1
                        
                conn.commit()

            elapsed = int(time.time() - start_time)
            try:
                bot.edit_message_text(
                    f"🔄 در حال پردازش...\n"
                    f"• کل کاربران: {total_users}\n"
                    f"• پردازش شده: {min(i + batch_size, total_users)}\n"
                    f"• موفق: {success}\n"
                    f"• ناموفق: {failed}\n"
                    f"⏳ زمان سپری شده: {elapsed} ثانیه",
                    chat_id=admin_id,
                    message_id=progress_msg.message_id
                )
            except:
                pass

        total_time = int(time.time() - start_time)
        report = (
            f"✅ عملیات با موفقیت تکمیل شد!\n\n"
            f"• کل کاربران: {total_users}\n"
            f"• ارسال موفق: {success}\n"
            f"• ارسال ناموفق: {failed}\n"
            f"⏱ زمان کل: {total_time} ثانیه"
        )
        
        bot.edit_message_text(
            report,
            chat_id=admin_id,
            message_id=progress_msg.message_id
        )

        log_admin_action(
            admin_id,
            "ارسال سکه همگانی",
            f"مقدار: {amount} | موفق: {success} | ناموفق: {failed}"
        )

    except ValueError:
        bot.reply_to(message, "  فقط عدد وارد کنید!")
    except Exception as e:
        error_msg = f"⚠️ خطای سیستمی: {str(e)}\n{traceback.format_exc()}"
        bot.reply_to(message, error_msg)
        print(error_msg)
        
admin_inputs = {}

def start_add_channel(message):
    admin_inputs[message.from_user.id] = {}
    msg = bot.send_message(message.chat.id, "مرحله 1️⃣:  `chat_id` کانال را وارد کنید:", parse_mode="Markdown")
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
        msg = bot.send_message(message.chat.id, " نام کانال نمی‌تواند خالی باشد. دوباره وارد کنید:")
        bot.register_next_step_handler(msg, get_title)
        return
    admin_inputs[message.from_user.id]["title"] = title
    msg = bot.send_message(message.chat.id, "مرحله 3️⃣: حالا `http://ble.ir/ لینک دعوت` کانال را وارد کنید:")
    bot.register_next_step_handler(msg, get_link)

def get_link(message):
    try:
        link = message.text.strip()
        
        if not link.startswith("http"):
            error_text = " لینک باید با http یا https شروع شود.  لینک صحیح وارد کنید:"
            msg = bot.send_message(
                chat_id=message.chat.id,
                text=error_text
            )
            bot.register_next_step_handler(msg, get_link)
            return
        
        admin_inputs[message.from_user.id]["link"] = link
        
        instruction_text = (
            "مرحله 4️⃣:  **زمان انقضا** را به صورت `HH:MM` وارد کنید:\n"
            "مثال: 23:59"
        )
        
        msg = bot.send_message(
            chat_id=message.chat.id,
            text=instruction_text,
            parse_mode="Markdown"
        )
        
        bot.register_next_step_handler(msg, get_expire_date)
    
    except Exception as e:
        print(f"خطا در get_link: {e}")
        bot.reply_to(message, " خطایی در پردازش رخ داد.")

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
        msg = bot.send_message(
            message.chat.id,
            "مثال 00:15 2:00 999999:00"
        )
        bot.register_next_step_handler(msg, get_expire_date)
    
    except Exception as e:
        admin_inputs.pop(message.from_user.id, None)
        bot.send_message(
            message.chat.id,
            f" خطای سیستمی: {str(e)}"
        )
def process_add_bot_inventory(message):
    try:
        amount = int(message.text.strip())
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE bot_inventory SET balance = balance + ? WHERE id = 1", (amount,))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, f"موجودی ربات به اندازه {amount} افزایش یافت.")
    except Exception as e:
        bot.send_message(message.chat.id, f"خطا در افزایش موجودی: {e}")

def process_reduce_bot_inventory(message):
    try:
        amount = int(message.text.strip())
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE bot_inventory SET balance = balance - ? WHERE id = 1", (amount,))
        conn.commit()
        conn.close()
        bot.send_message(message.chat.id, f"موجودی ربات به اندازه {amount} کاهش یافت.")
    except Exception as e:
        bot.send_message(message.chat.id, f"خطا در کاهش موجودی: {e}")

def process_add_balance(message):
    try:
        user_id, amount = map(int, message.text.split())
        with db_lock:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
            conn.commit()
            conn.close()
        bot.reply_to(message, f"✅ موجودی کاربر {user_id} به میزان {amount} تومان افزایش یافت.")
        log_admin_action(message.from_user.id, "افزایش موجودی", f"کاربر: {user_id} | مبلغ: {amount}")
    except Exception as e:
        bot.reply_to(message, " خطا! فرمت ورودی نامعتبر است. مثال صحیح: 12345 5000")

def process_reduce_balance(message):
    try:
        user_id, amount = map(int, message.text.split())
        with db_lock:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET balance = balance - ? WHERE user_id = ? AND balance >= ?", 
                          (amount, user_id, amount))
            if cursor.rowcount == 0:
                bot.reply_to(message, " موجودی کاربر کافی نیست یا شناسه نامعتبر است.")
            else:
                conn.commit()
                bot.reply_to(message, f"✅ موجودی کاربر {user_id} به میزان {amount} تومان کاهش یافت.")
                log_admin_action(message.from_user.id, "کاهش موجودی", f"کاربر: {user_id} | مبلغ: {amount}")
            conn.close()
    except Exception as e:
        bot.reply_to(message, " خطا! فرمت ورودی نامعتبر است. مثال صحیح: 12345 5000")

@bot.callback_query_handler(func=lambda call: call.data.startswith("user_info_exit"))
def admin_user_info_exit(call):
    try:
        _, unique_id = call.data.split("|")
        admin_user_info_results.pop(unique_id, None)
    except:
        admin_user_info_results.clear()  

    try:
        bot.edit_message_text("عملیات جستجو به پایان رسید.", call.message.chat.id, call.message.message_id)
    except:
        bot.send_message(call.message.chat.id, "عملیات جستجو به پایان رسید.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("user_info|"))
def admin_user_info_pagination(call):
    try:
        _, unique_id, page_str = call.data.split("|")
        page = int(page_str)
    except (ValueError, IndexError):
        return
    
    show_user_info_page(unique_id, page, call.message.chat.id, call.message.message_id)

def admin_add_gift(message):
    gift = message.text.strip()
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO gifts (gift) VALUES (?)", (gift,))
        conn.commit()
        conn.close()
    bot.reply_to(message, f"هدیه '{gift}' اضافه شد.")

def admin_edit_gift(message):
    try:
        gift_id, new_gift = message.text.strip().split(maxsplit=1)
        gift_id = int(gift_id)
    except Exception as e:
        bot.reply_to(message, "ورودی به درستی فرمت نشده است.  به این صورت وارد کنید: gift_id new_gift_code")
        return
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE gifts SET gift = ? WHERE id = ?", (new_gift, gift_id))
        conn.commit()
        conn.close()
    bot.reply_to(message, f"هدیه با شناسه {gift_id} به '{new_gift}' تغییر یافت.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("edit_coin|"))
def handle_edit_coin(call):
    if call.from_user.id not in ADMIN_IDS:
        return
    
    _, uid, page, unique_id = call.data.split("|")
    msg = bot.send_message(
        call.message.chat.id,
        f"مقدار جدید سکه برای کاربر {uid} را وارد کنید:",
    )
    bot.register_next_step_handler(msg, process_coin_edit, uid, page, unique_id)

def process_coin_edit(message, uid, page, unique_id):
    try:
        new_coin = int(message.text)
        with db_lock:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET coin_balance = ? WHERE user_id = ?",
                (new_coin, uid)
            )
            conn.commit()
            conn.close()
        bot.send_message(message.chat.id, f"✅ سکه کاربر {uid} به {new_coin} به‌روز شد.")
        show_user_info_page(unique_id, int(page), message.chat.id, message.message_id)
    except ValueError:
        bot.send_message(message.chat.id, " مقدار نامعتبر!")

@bot.callback_query_handler(func=lambda call: call.data.startswith("change_gender|"))
def handle_change_gender(call):
    if call.from_user.id not in ADMIN_IDS:
        return
    
    _, uid, page, unique_id = call.data.split("|")
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("پسر", callback_data=f"setgender_{uid}_پسر_{page}_{unique_id}"),
        types.InlineKeyboardButton("دختر", callback_data=f"setgender_{uid}_دختر_{page}_{unique_id}")
    )
    bot.send_message(call.message.chat.id, "جنسیت جدید را انتخاب کنید:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("setgender_"))
def process_gender_change(call):
    _, uid, gender, page, unique_id = call.data.split("_")
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET gender = ? WHERE user_id = ?",
            (gender, uid)
        )
        conn.commit()
        conn.close()
    bot.send_message(call.message.chat.id, f"✅ جنسیت کاربر {uid} به {gender} تغییر یافت.")
    show_user_info_page(unique_id, int(page), call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("ban_toggle|"))
def handle_ban_toggle(call):
    if call.from_user.id not in ADMIN_IDS:
        return
    
    _, uid, page, unique_id = call.data.split("|")
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM banned_users WHERE user_id = ?", (uid,))
        if cursor.fetchone():
            cursor.execute("DELETE FROM banned_users WHERE user_id = ?", (uid,))
            action = "آنبن"
        else:
            cursor.execute("INSERT INTO banned_users (user_id, ban_reason) VALUES (?, ?)", 
                          (uid, "بن دستی توسط ادمین"))
            action = "بن"
        conn.commit()
        conn.close()
    bot.send_message(call.message.chat.id, f"✅ کاربر {uid} {action} شد.")
    show_user_info_page(unique_id, int(page), call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("remove_waiting|"))
def handle_remove_waiting(call):
    if call.from_user.id not in ADMIN_IDS:
        return
    
    _, uid, page, unique_id = call.data.split("|")
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM waiting_users WHERE user_id = ?", (uid,))
        conn.commit()
        conn.close()
    bot.send_message(call.message.chat.id, f"✅ کاربر {uid} از لیست انتظار حذف شد.")
    show_user_info_page(unique_id, int(page), call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("delete_user|"))
def handle_delete_user(call):
    if call.from_user.id not in ADMIN_IDS:
        return
    
    _, uid, page, unique_id = call.data.split("|")
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE user_id = ?", (uid,))
        cursor.execute("DELETE FROM waiting_users WHERE user_id = ?", (uid,))
        cursor.execute("DELETE FROM active_chats WHERE user_id = ?", (uid,))
        cursor.execute("DELETE FROM banned_users WHERE user_id = ?", (uid,))
        conn.commit()
        conn.close()
    bot.send_message(call.message.chat.id, f" کاربر {uid} به طور کامل حذف شد.")
    show_user_info_page(unique_id, int(page), call.message.chat.id, call.message.message_id)

admin_user_info_results = {}

def show_user_info_page(unique_id, page, chat_id, message_id):
    results = admin_user_info_results.get(unique_id)
    if not results:
        bot.edit_message_text("نتایج جستجو منقضی شده است.", chat_id, message_id)
        return

    total = len(results)
    if page < 0:
        page = 0
    elif page >= total:
        page = total - 1

    uid, coin_balance, balance, gender, extra = results[page]
    text = f"👤 اطلاعات کاربر {uid}:\n"
    text += f" - 🪙 سکه: {coin_balance}\n - 💰 موجودی: {balance}\n - 👤 جنسیت: {gender}\n"
    if extra:
        text += extra

    markup = types.InlineKeyboardMarkup(row_width=2)

    markup.add(
        types.InlineKeyboardButton("🪙 ویرایش سکه", callback_data=f"edit_coin|{uid}|{page}|{unique_id}"),
        types.InlineKeyboardButton("💰 ویرایش موجودی", callback_data=f"edit_balance|{uid}|{page}|{unique_id}"),
    )
    markup.add(
        types.InlineKeyboardButton("🔄 تغییر جنسیت", callback_data=f"change_gender|{uid}|{page}|{unique_id}"),
        types.InlineKeyboardButton("⛔ بن/آنبن", callback_data=f"ban_toggle|{uid}|{page}|{unique_id}")
    )
    markup.add(
        types.InlineKeyboardButton("🧹 حذف از انتظار", callback_data=f"remove_waiting|{uid}|{page}|{unique_id}"),
        types.InlineKeyboardButton(" حذف کامل کاربر", callback_data=f"delete_user|{uid}|{page}|{unique_id}")
    )

    navigation = []
    if page > 0:
        navigation.append(types.InlineKeyboardButton("⬅️ قبلی", callback_data=f"user_info|{unique_id}|{page-1}"))
    if page < total - 1:
        navigation.append(types.InlineKeyboardButton("➡️ بعدی", callback_data=f"user_info|{unique_id}|{page+1}"))
    if navigation:
        markup.add(*navigation)

    markup.add(types.InlineKeyboardButton(" خروج", callback_data=f"user_info_exit|{unique_id}"))

    try:
        bot.edit_message_text(text, chat_id, message_id, reply_markup=markup)
    except Exception as e:
        print(f"خطا در ویرایش پیام: {e}")
        bot.send_message(chat_id, text, reply_markup=markup)

def admin_get_user_full_info(message):
    input_str = message.text.strip()
    clauses = []
    params = []
    
    if input_str.isdigit():
        clauses.append("user_id = ?")
        params.append(int(input_str))
    elif input_str in ["پسر", "دختر"]:
        clauses.append("gender = ?")
        params.append(input_str)

    else:
        filters = [f.strip() for f in input_str.split(",")]
        for cond in filters:
            if ":" not in cond:
                bot.reply_to(message, f"فرمت شرط '{cond}' نادرست است.  از فرمت key:value استفاده کنید.")
                return
            key, value = cond.split(":", 1)
            key = key.strip().lower()
            value = value.strip()
            if key == "user_id":
                try:
                    uid = int(value)
                except ValueError:
                    bot.reply_to(message, "شناسه کاربر باید عددی باشد!")
                    return
                clauses.append("user_id = ?")
                params.append(uid)
            elif key in ["balance", "coin_balance"]:
                op = "="
                if value[0] in ['>', '<', '=']:
                    op = value[0]
                    num_str = value[1:].strip()
                else:
                    num_str = value
                try:
                    num_val = float(num_str)
                except ValueError:
                    bot.reply_to(message, f"مقدار {key} باید عددی باشد!")
                    return
                clauses.append(f"{key} {op} ?")
                params.append(num_val)
            elif key == "gender":
                clauses.append("gender = ?")
                params.append(value)
            else:
                bot.reply_to(message, f"فیلتر '{key}' پشتیبانی نمی‌شود!")
                return

    if not clauses:
        bot.reply_to(message, "هیچ فیلتر معتبری وارد نشده است.")
        return

    where_clause = " AND ".join(clauses)
    query = f"SELECT user_id, coin_balance, balance, gender FROM users WHERE {where_clause}"
    
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(query, params)
        user_rows = cursor.fetchall()
        conn.close()

    if not user_rows:
        bot.reply_to(message, "هیچ کاربری مطابق با این فیلتر یافت نشد.")
        return
    
    results = []
    for row in user_rows:
        uid, coin_balance, balance, gender = row
        extra = ""
        with db_lock:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT desired_gender, join_time FROM waiting_users WHERE user_id = ?", (uid,))
            waiting_info = cursor.fetchone()
            conn.close()
        if waiting_info:
            desired_gender, join_time = waiting_info
            extra += f"\n - وضعیت انتظار: ترجیح شریک: {desired_gender}, زمان ورود: {join_time}"
        with db_lock:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT partner_id FROM active_chats WHERE user_id = ?", (uid,))
            active_chat = cursor.fetchone()
            conn.close()
        if active_chat:
            extra += f"\n - در چت با کاربر: {active_chat[0]}"
        with db_lock:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT partner_id FROM last_chat WHERE user_id = ?", (uid,))
            last_chat = cursor.fetchone()
            conn.close()
        if last_chat:
            extra += f"\n - آخرین چت با کاربر: {last_chat[0]}"
        with db_lock:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT ban_reason FROM banned_users WHERE user_id = ?", (uid,))
            banned = cursor.fetchone()
            conn.close()
        if banned:
            extra += f"\n - وضعیت بن: {banned[0]}"
        with db_lock:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT referral_code FROM referral_links WHERE user_id = ?", (uid,))
            referral = cursor.fetchone()
            conn.close()
        if referral:
            extra += f"\n - کد رفرال: {referral[0]}"
        with db_lock:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT referral_code FROM money_referral_links WHERE user_id = ?", (uid,))
            money_ref = cursor.fetchone()
            conn.close()
        if money_ref:
            extra += f"\n - کد رفرال مالی: {money_ref[0]}"
        with db_lock:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT blocked_id FROM blocked_users WHERE blocker_id = ?", (uid,))
            blocked_by = cursor.fetchall()
            conn.close()
        if blocked_by:
            blocked_ids = ", ".join(str(x[0]) for x in blocked_by)
            extra += f"\n - کاربران بلاک شده: {blocked_ids}"
        with db_lock:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT blocker_id FROM blocked_users WHERE blocked_id = ?", (uid,))
            blocked_for = cursor.fetchall()
            conn.close()
        if blocked_for:
            blocked_for_ids = ", ".join(str(x[0]) for x in blocked_for)
            extra += f"\n - بلاک شده توسط: {blocked_for_ids}"
        
        results.append((uid, coin_balance, balance, gender, extra))

    unique_id = generate_unique_id()
    admin_user_info_results[unique_id] = results

    show_user_info_page(unique_id, 0, message.chat.id, message.message_id)
def generate_unique_id(length=8):
    return ''.join(random.choices(string.ascii_letters + string.digits, k=length))

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

def log_admin_action(admin_id, action, details=""):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO admin_logs (admin_id, action, details) VALUES (?, ?, ?)", (admin_id, action, details))
        conn.commit()
        conn.close()

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


def admin_view_logs(call):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT admin_id, action, details, timestamp FROM admin_logs ORDER BY timestamp DESC LIMIT 20")
        logs = cursor.fetchall()
        conn.close()
    text = "آخرین لاگ‌ها:\n"
    for log in logs:
        text += f"[{log[3]}] Admin {log[0]}: {log[1]} - {log[2]}\n"
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
            bot.reply_to(message, " مقدار باید بزرگتر از صفر باشد!")
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
        bot.reply_to(message, "  یک عدد معتبر وارد کنید!")

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
        bot.send_message(message.chat.id, "خطا در فرمت ورودی.  به‌درستی وارد کنید: user_id amount")

def reduce_coins(message):
    try:
        user_id, amount = map(int, message.text.split())
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET coin_balance = coin_balance - ? WHERE user_id = ? AND coin_balance >= ?", (amount, user_id, amount))
        if cursor.rowcount == 0:
            bot.send_message(message.chat.id, " کاربر سکه کافی برای کاهش ندارد یا شناسه نامعتبر است.")
        else:
            conn.commit()
            bot.send_message(message.chat.id, f" {amount} سکه از کاربر {user_id} کسر شد.")
            bot.send_message(user_id, f"✅ سکه شما به مقدار {amount} کاهش یافت")
        conn.close()
    except:
        bot.send_message(message.chat.id, "خطا در فرمت ورودی.  به‌درستی وارد کنید: user_id amount")

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
        bot.reply_to(message, "خطا در افزایش موجودی.  فرمت ورودی را درست وارد کنید.")

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
        bot.reply_to(message, "خطا در کاهش موجودی.  فرمت ورودی را درست وارد کنید.")

def broadcast_message(message):
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

        if idx % 10 == 0 or idx == total_users:
            elapsed = int(time.time() - start_time)
            try:
                bot.edit_message_text(
                    f"در حال ارسال پیام...\nکل کاربران: {total_users}\nپردازش شده: {idx}\nارسال موفق: {success}\nارسال ناموفق: {failed}\nکاربران بلاک شده: {blocked}\nزمان: {elapsed} ثانیه",
                    message.chat.id, progress_msg.message_id
                )
            except Exception as e:
                pass

    total_time = int(time.time() - start_time)
    bot.reply_to(message, 
                 f"ارسال پیام به همه کاربران به پایان رسید.\nکل کاربران: {total_users}\nارسال موفق: {success}\nارسال ناموفق: {failed}\nکاربران بلاک شده: {blocked}\nزمان کل: {total_time} ثانیه")

def admin_referrals_page(call, page=0):
    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT referral_code, user_id FROM referral_links LIMIT 10 OFFSET ?", (page * 10,))
        rows = cursor.fetchall()
        cursor.execute("SELECT COUNT(*) FROM referral_links")
        total_referrals = cursor.fetchone()[0]
        conn.close()

    markup = types.InlineKeyboardMarkup()
    if rows:
        text = f"📋 لیست کدهای رفرال - صفحه {page+1}:\n\n"
        for idx, (code, user_id) in enumerate(rows, start=1 + page * 10):
            with db_lock:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM used_referrals WHERE referral_code = ?", (code,))
                usage_count = cursor.fetchone()[0]
                conn.close()

            text += f"{idx}. 👤 کاربر: {user_id} | 🏷️ کد: {code} | استفاده: {usage_count}\n"
            markup.add(
                types.InlineKeyboardButton(f"🗑️ حذف {code}", callback_data=f"referral_delete|{code}|{page}")
            )
    else:
        text = " هیچ کد رفرالی یافت نشد."

    buttons = []
    if page > 0:
        buttons.append(types.InlineKeyboardButton("⬅️ قبلی", callback_data=f"admin_referrals_page_{page-1}"))
    if (page + 1) * 10 < total_referrals:
        buttons.append(types.InlineKeyboardButton("➡️ بعدی", callback_data=f"admin_referrals_page_{page+1}"))

    if buttons:
        markup.add(*buttons)

    markup.add(types.InlineKeyboardButton(" خروج", callback_data="admin_referrals_exit"))

    try:
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=markup)
    except Exception as e:
        print("خطا در ویرایش پیام:", e)
        bot.send_message(call.message.chat.id, text, reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("referral_delete|"))
def handle_referral_delete(call):
    parts = call.data.split("|")
    if len(parts) < 3:
        return

    code = parts[1]
    try:
        page = int(parts[2])
    except ValueError:
        page = 0

    with db_lock:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM referral_links WHERE referral_code = ?", (code,))
        conn.commit()
        conn.close()

    bot.send_message(call.message.chat.id,f"حله {code}")
    admin_referrals_page(call, page=page)

@bot.callback_query_handler(func=lambda call: call.data == "admin_referrals_exit")
def handle_referrals_exit(call):
    bot.edit_message_text(" عملیات مشاهده کدهای رفرال به پایان رسید.", call.message.chat.id, call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("admin_referrals"))
def admin_referrals_handler(call):
    if call.data == "admin_referrals":
        admin_referrals_page(call, page=0)
    elif call.data.startswith("admin_referrals_page_"):
        try:
            page = int(call.data.split("admin_referrals_page_")[-1])
        except ValueError:
            page = 0
        admin_referrals_page(call, page=page)

if __name__ == "__main__":
    print("✅ ربات فعال شد!")
    bot.infinity_polling(timeout=30)