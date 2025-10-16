import os
import json
import asyncio
from flask import Flask, request
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from parser import get_journal_with_cookie, extract_grades_from_html

# --- Настройки ---
BOT_TOKEN = os.getenv("BOT_TOKEN")
APP_URL = os.getenv("APP_URL")

if not BOT_TOKEN or not APP_URL:
    raise ValueError("❌ BOT_TOKEN или APP_URL не заданы!")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

COOKIE_FILE = "cookies.json"
if not os.path.exists(COOKIE_FILE):
    with open(COOKIE_FILE, "w") as f:
        json.dump({}, f)

# --- Cookie helper ---
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

# --- Aiogram handlers ---
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer(
        "👋 Привет!\n"
        "Отправь мне свои cookies (например, `college_session=...; XSRF-TOKEN=...`), "
        "и я покажу твои оценки.\n\n"
        "Если не знаешь, как их получить — скоро появится инструкция 🔧",
        parse_mode="Markdown"
    )

@dp.message()
async def handle_cookie(message: types.Message):
    user_id = message.from_user.id
    cookie_string = message.text.strip()

    await message.answer("🔐 Cookie получена, проверяю...")

    save_cookie(user_id, cookie_string)
    html = await get_journal_with_cookie(cookie_string)

    if not html:
        await message.answer("❌ Cookie неверна или устарела.")
        return

    grades = extract_grades_from_html(html)
    if not grades:
        await message.answer("⚠️ Оценки не найдены.")
    else:
        await message.answer(grades, parse_mode="Markdown")

# --- Flask сервер ---
flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return "<h1>🤖 Бот работает на Render!</h1>", 200

@flask_app.route(f"/webhook/{BOT_TOKEN}", methods=["POST"])
async def webhook():
    data = request.get_json(force=True)
    update = types.Update(**data)

    # Вместо await — создаем задачу внутри текущего event loop
    asyncio.create_task(dp.feed_update(bot, update))

    return "ok", 200


# --- Запуск ---
async def on_startup():
    await bot.set_webhook(f"{APP_URL}/webhook/{BOT_TOKEN}", drop_pending_updates=True)
    print(f"✅ Webhook установлен: {APP_URL}/webhook/{BOT_TOKEN}")

def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(on_startup())
    flask_app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))

if __name__ == "__main__":
    main()
