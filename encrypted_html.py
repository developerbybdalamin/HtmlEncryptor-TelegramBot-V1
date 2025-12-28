import base64
import os
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from flask import Flask
import threading
import asyncio

# ================= FLASK APP FOR RENDER =================
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 HTML Protect Bot is Running!"

@app.route('/health')
def health():
    return "OK", 200

# ================= CONFIG =================
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8333140157:AAE-Fcar3AopSYeBpMG5KNSurUyq7M3Cp2U")
COUNT_FILE = "count.txt"
PORT = int(os.environ.get("PORT", 8080))

# ================= COUNTER =================
def next_id():
    if not os.path.exists(COUNT_FILE):
        with open(COUNT_FILE, "w") as f:
            f.write("1")
        return 1
    with open(COUNT_FILE, "r+") as f:
        n = int(f.read())
        f.seek(0)
        f.write(str(n + 1))
        f.truncate()
    return n

import binascii

# ================= ENCRYPT =================
def to_hex(s):
    return binascii.hexlify(s.encode()).decode()

# ================= PROTECT HTML =================
def protect_html(html):
    # Step 1: URL Encode (to handle special characters)
    import urllib.parse
    encoded_html = urllib.parse.quote(html)
    
    # Step 2: Base64
    b64 = base64.b64encode(encoded_html.encode()).decode()
    
    # Step 3: Hex
    hex_data = to_hex(b64)
    
    # ফাইল সাইজ বাড়ানোর জন্য গারবেজ ডেটা মিক্সিং (সংযুক্ত ফাইলের মতো)
    # আমরা ডেটা ব্লককে চাঙ্ক করে সেগুলোর মাঝে গারবেজ ক্যারেক্টার ঢোকাবো
    def add_junk(data):
        result = ""
        for i in range(0, len(data), 2):
            result += data[i:i+2]
            if random.random() > 0.7:
                result += random.choice("ghijklmnopqrstuvwxyz") # Non-hex chars as junk
        return result

    final_data = add_junk(hex_data)
    
    # চাঙ্কগুলোতে ভাগ করা (জাভাস্ক্রিপ্ট ভেরিয়েবল হিসেবে)
    chunk_size = 2000
    chunks = [final_data[i:i+chunk_size] for i in range(0, len(final_data), chunk_size)]
    
    # জাভাস্ক্রিপ্ট ভেরিয়েবল তৈরি করা (_d0, _d1, etc.)
    js_vars = ""
    var_names = []
    for i, chunk in enumerate(chunks):
        var_name = f"_d{i}"
        js_vars += f'    var {var_name}="{chunk}";\n'
        var_names.append(var_name)
    
    raw_assembly = "+".join(var_names)

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Secure Loading...</title>
    <style>
        html, body {{ height: 100%; margin: 0; padding: 0; background: #000; overflow: hidden; }}
        #secure-load-screen {{
            display: flex; flex-direction: column; align-items: center; justify-content: center;
            height: 100%; color: #00ff41; font-family: monospace; z-index: 9999; position: fixed; width: 100%; top: 0; left: 0;
        }}
        .spinner {{
            width: 40px; height: 40px; border: 4px solid #333; border-top: 4px solid #00ff41; border-radius: 50%;
            animation: spin 1s linear infinite; margin-bottom: 20px;
        }}
        @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
    </style>
</head>
<body>

<div id="secure-load-screen">
    <div class="spinner"></div>
    <div id="status">INITIALIZING SECURITY...</div>
</div>

<script>
(function(){{
    // 1. Anti-Bot / Anti-Headless Detection
    var isBot = false;
    if (navigator.webdriver || !navigator.languages || navigator.languages.length === 0) isBot = true;
    if (window.chrome && !window.chrome.runtime) isBot = false; // Simple bypass for some, but bots often fail this
    if (isBot) {{
        document.body.innerHTML = "<div style='color:red;padding:20px;text-align:center'><h1>FUCK YOU CRACKER 😂👆</h1><p>বোকাচোদা সখ কত crack চোদাইতে আইছোচ 😂😂😂</p></div>";
        return;
    }}

    // 2. Extra verification to stop Playwright/Puppeteer
    try {{
        if (Object.getOwnPropertyDescriptor(navigator, 'webdriver')) isBot = true;
    }} catch(e) {{}}

    if (isBot) {{
        document.body.innerHTML = "";
        return;
    }}

{js_vars}
    var _raw = {raw_assembly};

    setTimeout(function(){{
        try {{
            // Double check for bots before final execution
            if (window.outerWidth === 0 && window.outerHeight === 0) return;

            document.getElementById("status").innerText = "DECRYPTING DATA...";
            
            // Clean Junk
            var _cleanHex = _raw.replace(/[^0-9a-fA-F]/g, "");

            // Decode Hex -> Base64
            var _base64 = "";
            for (var i = 0; i < _cleanHex.length; i += 2) {{
                _base64 += String.fromCharCode(parseInt(_cleanHex.substr(i, 2), 16));
            }}

            var _finalHtml = decodeURIComponent(atob(_base64));

            document.documentElement.removeAttribute("style");
            document.body.removeAttribute("style");
            document.body.innerHTML = "";

            document.open();
            document.write(_finalHtml);
            document.close();

        }} catch (e) {{
            document.body.innerHTML = "<h3 style='color:red;text-align:center'>Security Violation</h3>";
        }}
    }}, 2000);
}})();
</script>
</body>
</html>"""

# ================= START =================
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    kb = [
        [InlineKeyboardButton("🔐 Protect HTML", callback_data="protect")]
    ]
    await update.message.reply_text(
        "🔐 Welcome to HTML Protector Bot\n\nSend HTML file to protect it",
        reply_markup=InlineKeyboardMarkup(kb)
    )

# ================= CALLBACK =================
async def callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    
    if q.data == "protect":
        ctx.user_data["mode"] = "protect"
        await q.message.reply_text("📄 Send your HTML file to protect it\n\nDeveloped by @BDALAMINHACKER")

# ================= FILE HANDLER =================
async def file_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if ctx.user_data.get("mode") != "protect":
        return

    msg = await update.message.reply_text("⏳ Processing your file, please wait...")

    doc = update.message.document
    f = await doc.get_file()

    inp = "input.html"
    out = f"protected_{next_id()}.html"

    await f.download_to_drive(inp)

    with open(inp, "r", encoding="utf-8", errors="ignore") as file:
        html = file.read()

    protected = protect_html(html)

    with open(out, "w", encoding="utf-8") as file:
        file.write(protected)

    await update.message.reply_document(
        document=open(out, "rb"),
        caption="✅ HTML Protected (Max Security)\n\nDeveloped by @BDALAMINHACKER"
    )

    await msg.delete()
    os.remove(inp)
    os.remove(out)
    ctx.user_data.clear()

# ================= TELEGRAM BOT SETUP =================
def setup_bot():
    """Setup and run the Telegram bot"""
    app_bot = Application.builder().token(BOT_TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(CallbackQueryHandler(callback))
    app_bot.add_handler(MessageHandler(filters.Document.ALL, file_handler))
    
    print("🤖 HTML Protect Bot Starting...")
    return app_bot

# ================= MAIN =================
def run_flask():
    """Run Flask server"""
    print(f"🌐 Flask server starting on port {PORT}...")
    app.run(host='0.0.0.0', port=PORT, debug=False, use_reloader=False)

def main():
    # Start Flask server in a separate thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Setup and run Telegram bot
    bot_app = setup_bot()
    
    print("🚀 Bot and server are running!")
    print(f"🤖 Bot Token: {BOT_TOKEN[:10]}...")
    print(f"🌐 Web Server: http://0.0.0.0:{PORT}")
    
    # Run bot with polling
    bot_app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()