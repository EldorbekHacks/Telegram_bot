import re
import os
from transliterate import translit
import telebot
from telebot import types
from gtts import gTTS
from fpdf import FPDF

# ================== BOSHLANG'ICH SOZLAMALAR ==================
TOKEN = "BOT-Token"  # BotFather'dan token ol
bot = telebot.TeleBot(TOKEN)

CHANNEL_USERNAME = "@study_in_japanes"
user_stats = {}      # Foydalanuvchi statistikasi
user_logs = {}       # Foydalanuvchi xabarlari
blocked_words = ["spam", "reklama", "botlar"]  # Spam so'zlar

# ================== TRANSLITERATSIYA FUNKSIYALARI ==================
def to_cyrillic(text):
    return translit(text, 'ru')

def to_latin(text):
    return translit(text, 'ru', reversed=True)

def is_latin(text):
    return not re.search('[а-яА-ЯёЁ]', text)

# ================== FOYDALANUVCHI FUNKSIYALARI ==================
def is_user_member(user_id):
    try:
        member = bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ['member', 'administrator', 'creator']
    except:
        return False

def update_stats(user_id):
    if user_id not in user_stats:
        user_stats[user_id] = 0
    user_stats[user_id] += 1

def log_message(user_id, username, text):
    if user_id not in user_logs:
        user_logs[user_id] = []
    user_logs[user_id].append(text)
    with open("bot_logs.txt", "a", encoding="utf-8") as f:
        f.write(f"{user_id} @{username or 'username_yoq'}: {text}\n")

def text_to_audio(text, filename):
    tts = gTTS(text=text, lang='ru')  # rus tilida audio yaratish
    tts.save(filename)


def create_pdf(user_id):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    logs = user_logs.get(user_id, [])
    if not logs:
        pdf.cell(0, 10, "Hech qanday xabar topilmadi.", ln=True)
    else:
        pdf.multi_cell(0, 8, "\n".join(logs))
    filename = f"user_{user_id}_report.pdf"
    pdf.output(filename)
    return filename

# ================== BOT KOMANDALARI ==================
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.from_user.id
    if is_user_member(user_id):
        bot.reply_to(message, "Assalomu alaykum! Matn kiriting, men lotin ↔ kirillga o‘giraman.\n/help - Qo‘llanma uchun")
    else:
        markup = types.InlineKeyboardMarkup()
        join_btn = types.InlineKeyboardButton("Kanalga qo‘shilish", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")
        markup.add(join_btn)
        bot.send_message(user_id, "Iltimos, avval kanalga qo‘shiling!", reply_markup=markup)

@bot.message_handler(commands=['help'])
def help_message(message):
    text = (
        "👋 Assalomu alaykum!\n\n"
        "Bu bot matnni lotin ↔ kirill alifbosiga o‘giradi va audio faylga aylantiradi.\n"
        "Foydalanish:\n"
        "/start - Botni ishga tushirish\n"
        "/help - Qo‘llanma\n"
        "/stats - Sizning transliteratsiya statistikasi\n"
        "/report - PDF yoki matn hisobotini olish\n\n"
        "Matn yozing va u avtomatik transliteratsiya qilinadi."
    )
    bot.reply_to(message, text)

@bot.message_handler(commands=['stats'])
def stats(message):
    user_id = message.from_user.id
    count = user_stats.get(user_id, 0)
    bot.reply_to(message, f"Siz {count} marta matn transliteratsiya qildingiz.")

@bot.message_handler(commands=['report'])
def report(message):
    user_id = message.from_user.id
    pdf_file = create_pdf(user_id)
    with open(pdf_file, "rb") as f:
        bot.send_document(user_id, f)
    os.remove(pdf_file)

# ================== MATN QABUL QILISH VA TRANSLITERATSIYA ==================
@bot.message_handler(func=lambda m: True)
def convert(message):
    user_id = message.from_user.id
    username = message.from_user.username or "username_yoq"

    if any(word in message.text.lower() for word in blocked_words):
        bot.reply_to(message, "❌ Bu xabar qabul qilinmaydi.")
        return

    if not is_user_member(user_id):
        markup = types.InlineKeyboardMarkup()
        join_btn = types.InlineKeyboardButton("Kanalga qo‘shilish", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")
        markup.add(join_btn)
        bot.send_message(user_id, "Iltimos, avval kanalga qo‘shiling!", reply_markup=markup)
        return

    text = message.text
    update_stats(user_id)
    log_message(user_id, username, text)

    if is_latin(text):
        converted = to_cyrillic(text)
    else:
        converted = to_latin(text)

    bot.reply_to(message, converted)

    # Audio fayl yaratish
    audio_filename = f"user_{user_id}.mp3"
    text_to_audio(converted, audio_filename)
    with open(audio_filename, "rb") as f:
        bot.send_audio(user_id, f)
    os.remove(audio_filename)

# ================== BOTNI ISHGA TUSHIRISH ==================
bot.polling()
