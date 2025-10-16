import os
import json
from flask import Flask, request
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from parser import get_journal_with_cookie, extract_grades_from_html
import asyncio

BOT_TOKEN = os.getenv("BOT_TOKEN")
APP_URL = os.getenv("APP_URL")

if not BOT_TOKEN or not APP_URL:
    raise ValueError("❌ BOT_TOKEN или APP_URL не заданы!")

COOKIE_FILE = "cookies.json"
if not os.path.exists(COOKIE_FILE):
    with open(COOKIE_FILE, "w") as f:
        json.dump({}, f)

def save_cookie(user_id, cookie):
    with open(COOKIE_FILE, "r+", encoding="utf-8") as f:
        data = json.load(f)
        data[str(user_id)] = cookie
        f.seek(0)
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.truncate()

def load_cookie(user_id):
    with open(COOKIE_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data.get(str(user_id))

# --- Telegram Handlers ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📖 Как получить cookie", url=f"{APP_URL}/how_to_cookie")]
    ]
    await update.message.reply_text(
        "👋 Привет! Отправь свою cookie (например, `college_session=...; XSRF-TOKEN=...`), "
        "и я покажу твои оценки.\n\n"
        "Если не знаешь, как получить cookie — нажми кнопку ниже 👇",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_cookie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    cookie_string = update.message.text.strip()
    save_cookie(user_id, cookie_string)
    await update.message.reply_text("✅ Cookie сохранена! Проверяю журнал...")

    html = await get_journal_with_cookie(cookie_string)
    if not html:
        await update.message.reply_text("❌ Не удалось войти. Cookie устарела или неверна.")
        return

    grades = extract_grades_from_html(html)
    await update.message.reply_text(grades or "📭 Оценок не найдено.", parse_mode="Markdown")

async def refresh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    cookie = load_cookie(user_id)

    if not cookie:
        await update.message.reply_text("⚠️ У тебя нет сохранённой cookie. Отправь новую.")
        return

    await update.message.reply_text("♻️ Обновляю данные журнала...")

    html = await get_journal_with_cookie(cookie)
    if not html:
        await update.message.reply_text("❌ Cookie устарела, отправь новую.")
        return

    grades = extract_grades_from_html(html)
    await update.message.reply_text(grades or "📭 Оценок не найдено.", parse_mode="Markdown")

# --- Flask App ---
app = Flask(__name__)

@app.route("/")
def home():
    return "<h1>🤖 Бот работает на Render!</h1>", 200

@app.route(f"/webhook/{BOT_TOKEN}", methods=["POST"])
def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, tg_app.bot)
    asyncio.run(tg_app.process_update(update))
    return "ok", 200

# --- Telegram App ---
tg_app = Application.builder().token(BOT_TOKEN).build()
tg_app.add_handler(CommandHandler("start", start))
tg_app.add_handler(CommandHandler("refresh", refresh))
tg_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_cookie))

if __name__ == "__main__":
    import threading

    async def set_webhook():
        await tg_app.bot.set_webhook(f"{APP_URL}/webhook/{BOT_TOKEN}", drop_pending_updates=True)

    asyncio.run(set_webhook())

    # Flask запускаем в отдельном потоке
    threading.Thread(target=lambda: app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))).start()

    print("🚀 Flask + Telegram Webhook запущены успешно.")
