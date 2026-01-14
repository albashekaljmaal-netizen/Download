import telebot
import requests
import re
from bs4 import BeautifulSoup
from telebot import types
import os

# --- الإعدادات الأساسية ---
TOKEN = "8112995930:AAHJ4OqNLk-9y7A1pUPELQVOhAmerczeIR8"
bot = telebot.TeleBot(TOKEN)
user_data = {}

# --- دالة فحص محتوى الموقع وملفاته ---
def get_site_data(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        combined_content = response.text # محتوى HTML الأساسي
        
        # استخراج روابط ملفات JS, CSS, PHP, JSON
        assets = []
        for tag in soup.find_all(['script', 'link', 'a']):
            link = tag.get('src') or tag.get('href')
            if link:
                if link.startswith('/'):
                    link = url.rstrip('/') + link
                if any(link.endswith(ext) for ext in ['.js', '.css', '.php', '.json']):
                    assets.append(link)
        
        # فحص أول 15 ملفاً لضمان السرعة
        for asset_url in list(set(assets))[:15]:
            try:
                asset_res = requests.get(asset_url, headers=headers, timeout=5)
                combined_content += f"\n\n/* --- Content from: {asset_url} --- */\n"
                combined_content += asset_res.text
            except:
                continue
        return combined_content
    except Exception as e:
        return f"Error: {str(e)}"

# --- أوامر البوت ---
@bot.message_handler(commands=['start'])
def start(message):
    welcome_text = (
        "صلى على نبي محمد ﷺ\n\n"
        "مرحباً بك في بوت URL INFORMATION 🌐\n"
        "أرسل رابط الموقع الذي تريد فحصه الآن مباشرة:"
    )
    bot.reply_to(message, welcome_text)

@bot.message_handler(func=lambda message: True)
def handle_link(message):
    url = message.text.strip()
    if not url.startswith("http"):
        bot.reply_to(message, "❌ الرابط غير صحيح! يجب أن يبدأ بـ http أو https")
        return

    user_data[message.chat.id] = url
    
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton("بحث عميق Admin Panel 🛠", callback_data="scan_admin")
    btn2 = types.InlineKeyboardButton("استخراج الروابط URL Extractor 🔗", callback_data="scan_urls")
    markup.add(btn1)
    markup.add(btn2)
    
    bot.reply_to(message, f"🔗 الرابط المستهدف: {url}\nاختر نوع الفحص المطلوب أدناه:", reply_markup=markup)

# --- معالجة طلبات الفحص ---
@bot.callback_query_handler(func=lambda call: call.data in ["scan_admin", "scan_urls"])
def execute_scan(call):
    bot.answer_callback_query(call.id, "⏳ جاري بدء الفحص...")
    
    target_url = user_data.get(call.message.chat.id)
    if not target_url:
        bot.send_message(call.message.chat.id, "❌ حدث خطأ، يرجى إعادة إرسال الرابط.")
        return

    bot.edit_message_text(f"🚀 جاري الفحص العميق واستخراج البيانات من الموقع...\nيرجى الانتظار.", 
                          call.message.chat.id, call.message.message_id)
    
    site_content = get_site_data(target_url)
    domain_name = target_url.split("//")[-1].split("/")[0].replace(".", "_")

    if call.data == "scan_admin":
        admin_patterns = [r'admin', r'login', r'panel', r'wp-admin', r'dashboard', r'manage', r'auth', r'control']
        found_paths = []
        for p in admin_patterns:
            matches = re.findall(r'/[^"\'\s]*' + p + r'[^"\'\s]*', site_content, re.IGNORECASE)
            found_paths.extend(matches)
        
        found_paths = list(set(found_paths))
        file_path = f"{domain_name}_admin_panel.js"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"// Scan Results for Admin Panels: {target_url}\n\n")
            f.write("\n".join(found_paths) if found_paths else "// No results found.")
        
        with open(file_path, "rb") as doc:
            bot.send_document(call.message.chat.id, doc, caption=f"✅ نتائج Admin Panel لـ {domain_name}")
        os.remove(file_path)

    elif call.data == "scan_urls":
        extracted_urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-f_A-F][0-9a-f_A-F]))+', site_content)
        extracted_urls = list(set(extracted_urls))
        
        file_path = f"{domain_name}_url_extractor.js"
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(f"// Extracted URLs from: {target_url}\n\n")
            f.write("\n".join(extracted_urls) if extracted_urls else "// No URLs found.")
            
        with open(file_path, "rb") as doc:
            bot.send_document(call.message.chat.id, doc, caption=f"✅ الروابط المستخرجة لـ {domain_name}")
        os.remove(file_path)

# --- تشغيل البوت ---
print("--- البوت الآن يعمل بدون اشتراك إجباري ---")
bot.infinity_polling()
