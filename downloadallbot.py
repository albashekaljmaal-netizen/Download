import telebot
import yt_dlp
import os

# إعدادات البوت
TOKEN = "8112995930:AAHJ4OqNLk-9y7A1pUPELQVOhAmerczeIR8"
bot = telebot.TeleBot(TOKEN)

# حقوق المطور
DEV_INFO = "مع تحيات {المطور هيثم محمود الجمال}\n@albashekaljmaal"

# مجلد مؤقت للتحميل
DOWNLOAD_DIR = "downloads"
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

@bot.message_handler(commands=['start'])
def start(message):
    welcome_msg = f"👋 أهلاً بك في بوت التحميل الشامل!\n\nأرسل لي أي رابط وسأقوم بتحميله لك.\n\n⎯ ⎯ ⎯ ⎯ ⎯ ⎯ ⎯ ⎯\n{DEV_INFO}"
    bot.reply_to(message, welcome_msg)

@bot.message_handler(func=lambda message: message.text.startswith("http"))
def handle_download(message):
    url = message.text.strip()
    chat_id = message.chat.id
    
    status_msg = bot.reply_to(message, "⏳ جارِ معالجة الرابط والتحميل...")

    ydl_opts = {
        'format': 'best',
        'outtmpl': f'{DOWNLOAD_DIR}/%(title)s.%(ext)s',
        'max_filesize': 50 * 1024 * 1024,
        'quiet': True,
        'no_warnings': True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            if not os.path.exists(filename):
                filename = max([os.path.join(DOWNLOAD_DIR, f) for f in os.listdir(DOWNLOAD_DIR)], key=os.path.getctime)

            bot.edit_message_text(f"✅ اكتمل التحميل!\nجارِ الرفع الآن... 🚀", chat_id, status_msg.message_id)
            
            with open(filename, 'rb') as video:
                # إضافة الحقوق أسفل الفيديو المرسل
                caption_text = f"✨ تم التحميل بنجاح:\n📌 {info.get('title', 'Video')}\n\n⎯ ⎯ ⎯ ⎯ ⎯ ⎯ ⎯ ⎯\n{DEV_INFO}"
                bot.send_video(chat_id, video, caption=caption_text)

            os.remove(filename)
            bot.delete_message(chat_id, status_msg.message_id)

    except Exception as e:
        error_text = str(e)
        if "File is too large" in error_text:
            bot.edit_message_text(f"❌ الفيديو حجمه كبير جداً.\n\n{DEV_INFO}", chat_id, status_msg.message_id)
        else:
            bot.edit_message_text(f"❌ حدث خطأ: تأكد من صحة الرابط.\n\n{DEV_INFO}", chat_id, status_msg.message_id)
            # تنظيف المجلد من أي ملفات عالقة
            for f in os.listdir(DOWNLOAD_DIR):
                try: os.remove(os.path.join(DOWNLOAD_DIR, f))
                except: pass

if __name__ == "__main__":
    print("✅ البوت يعمل الآن باسم المطور هيثم محمود الجمال...")
    bot.infinity_polling()
