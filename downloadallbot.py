import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from io import BytesIO
from apscheduler.schedulers.background import BackgroundScheduler

BOT_TOKEN = os.environ.get("BOT_TOKEN")
RENDER_URL = "https://webreconbot.onrender.com/" 

admin_paths = ["admin","admin/login","wp-admin","administrator","cpanel","panel","dashboard"]
user_urls = {}

# وظيفة منع النوم (Keep-alive)
def keep_alive():
    try:
        requests.get(RENDER_URL, timeout=10)
        print("Keep-alive: Ping successful.")
    except Exception as e:
        print(f"Keep-alive error: {e}")

scheduler = BackgroundScheduler()
scheduler.add_job(keep_alive, "interval", minutes=10)
scheduler.start()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # تم تحديث حقوق المطور هنا
    welcome_text = """👋 مرحبا بك في بوت جمع معلومات المواقع..

🛠️ إعداد وتطوير: هيثم محمود الجمال
🔗 @albashekaljmaal3

🌐 ادخل رابط الموقع المستهدف المراد فحصه:
"""
    await update.message.reply_text(welcome_text)

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if not url.startswith("http"):
        url = "http://" + url
    user_urls[update.effective_user.id] = url

    keyboard = [
        [InlineKeyboardButton("🌐 معلومات الموقع", callback_data="info")],
        [InlineKeyboardButton("🔗 روابط الموقع", callback_data="links")],
        [InlineKeyboardButton("🛡️ Admin Panel", callback_data="admin")],
        [InlineKeyboardButton("☁️ Cloudflare", callback_data="cloudflare")],
        [InlineKeyboardButton("🧩 نوع النظام", callback_data="cms")],
        [InlineKeyboardButton("🌍 Subdomains", callback_data="subs")]
    ]
    await update.message.reply_text(f"تم استقبال الرابط: {url}\nاختر نوع الفحص:", reply_markup=InlineKeyboardMarkup(keyboard))

async def send_txt(chat_id, context, text):
    file = BytesIO()
    file.write(text.encode("utf-8"))
    file.seek(0)
    await context.bot.send_document(chat_id=chat_id, document=file, filename="scan_result.txt")

async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    url = user_urls.get(query.from_user.id)
    if not url:
        await query.message.reply_text("يرجى إرسال الرابط مرة أخرى.")
        return

    domain = urlparse(url).netloc
    result = ""

    try:
        if query.data == "info":
            data = requests.get(f"http://ip-api.com/json/{domain}", timeout=15).json()
            result = f"IP: {data.get('query')}\nCountry: {data.get('country')}\nISP: {data.get('isp')}\nCity: {data.get('city')}"
        
        elif query.data == "links":
            r = requests.get(url, timeout=15)
            soup = BeautifulSoup(r.text, "html.parser")
            links = set(urljoin(url, a['href']) for a in soup.find_all("a", href=True))
            result = "روابط الموقع المكتشفة:\n" + "\n".join(list(links)[:50])

        elif query.data == "admin":
            found = []
            for p in admin_paths:
                test = f"{url.rstrip('/')}/{p}"
                try:
                    res = requests.get(test, timeout=5)
                    if res.status_code == 200: found.append(test)
                except: pass
            result = "لوحات التحكم المكتشفة:\n" + ("\n".join(found) if found else "لم يتم العثور على لوحات مشهورة")

        elif query.data == "cloudflare":
            h = requests.get(url, timeout=15).headers
            result = "Cloudflare: مفعل" if "cloudflare" in str(h).lower() else "Cloudflare: غير مكتشف"

        elif query.data == "cms":
            r = requests.get(url, timeout=15).text
            result = "النظام: WordPress" if "wp-content" in r else "النظام: غير معروف أو برمجة خاصة"

        elif query.data == "subs":
            crt = requests.get(f"https://crt.sh/?q=%25.{domain}&output=json", timeout=20).json()
            subs = list(set([i["name_value"] for i in crt]))
            result = "النطاقات الفرعية (Subdomains):\n" + "\n".join(subs[:40])

    except Exception as e:
        result = f"حدث خطأ أثناء العملية: {e}"

    await send_txt(query.message.chat_id, context, result)

def main():
    application = ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))
    application.add_handler(CallbackQueryHandler(buttons))

    port = int(os.environ.get("PORT", 10000))
    
    application.run_webhook(
        listen="0.0.0.0",
        port=port,
        url_path=BOT_TOKEN,
        webhook_url=f"{RENDER_URL}{BOT_TOKEN}"
    )

if __name__ == "__main__":
    main()
