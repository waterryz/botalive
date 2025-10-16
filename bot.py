import os
import json
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, ContextTypes, filters
)
from parser import get_journal_with_cookie

BOT_TOKEN = os.getenv("BOT_TOKEN")
APP_URL = os.getenv("APP_URL")

if not BOT_TOKEN or not APP_URL:
    raise ValueError("❌ BOT_TOKEN или APP_URL не заданы!")

COOKIE_FILE = "cookies.json"
if not os.path.exists(COOKIE_FILE):
    with open(COOKIE_FILE, "w") as f:
        json.dump({}, f)

def save_cookie(user_id, cookie):
    with open(COOKIE_FILE, "r+") as f:
        data = json.load(f)
        data[str(user_id)] = cookie
        f.seek(0)
        json.dump(data, f)
        f.truncate()

def load_cookie(user_id):
    with open(COOKIE_FILE, "r") as f:
        data = json.load(f)
        return data.get(str(user_id))

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Отправь свою cookie (например, `college_session=...; XSRF-TOKEN=...`), "
        "и я покажу твои оценки.",
        parse_mode="Markdown"
    )

async def handle_cookie(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    cookie_string = update.message.text.strip()

    save_cookie(user_id, cookie_string)
    await update.message.reply_text("🔐 Cookie получена, проверяю...")

    html = await get_journal_with_cookie(cookie_string)

    if isinstance(html, list):  # если вернулся список — преобразуем в строку
        html = "\n".join(map(str, html))

    if not isinstance(html, str) or not html.strip():
        await update.message.reply_text("❌ Cookie неверна или устарела.")
        return

    await update.message.reply_text(html, parse_mode="Markdown")

async def refresh(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    cookie = load_cookie(user_id)

    if not cookie:
        await update.message.reply_text("⚠️ У тебя нет сохранённой cookie. Отправь её снова.")
        return

    await update.message.reply_text("♻️ Обновляю данные журнала...")

    html = await get_journal_with_cookie(cookie)

    if isinstance(html, list):
        html = "\n".join(map(str, html))

    if not isinstance(html, str) or not html.strip():
        await update.message.reply_text("❌ Cookie устарела, отправь новую.")
        return

    await update.message.reply_text(html, parse_mode="Markdown")

if __name__ == "__main__":
    print("🚀 Запуск Telegram-бота (polling mode)...")

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("refresh", refresh))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_cookie))

    app.run_polling(drop_pending_updates=True)
