import os
import asyncio
import json
from flask import Flask, request
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from parser import get_journal_with_cookie, extract_grades_from_html

# ==============================
# 🔧 НАСТРОЙКИ
# ==============================
BOT_TOKEN = os.getenv("BOT_TOKEN")
APP_URL = os.getenv("APP_URL")  # пример: https://botalive.onrender.com

if not BOT_TOKEN or not APP_URL:
    raise ValueError("❌ BOT_TOKEN или APP_URL не заданы в переменных окружения!")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
app = Flask(__name__)

COOKIE_FILE = "cookies.json"

# ==============================
# 💾 Работа с cookies
# ==============================
if not os.path.exists(COOKIE_FILE):
    with open(COOKIE_FILE, "w") as f:
        json.dump({}, f)


def save_cookie(user_id, cookie):
    """Сохраняет cookie пользователя"""
    with open(COOKIE_FILE, "r+") as f:
        data = json.load(f)
        data[str(user_id)] = cookie
        f.seek(0)
        json.dump(data, f, indent=2)
        f.truncate()


def load_cookie(user_id):
    """Загружает cookie пользователя"""
    with open(COOKIE_FILE, "r") as f:
        data = json.load(f)
        return data.get(str(user_id))


# ==============================
# 💬 Telegram-хэндлеры
# ==============================
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer(
        "👋 Привет!\n\n"
        "Этот бот показывает твои оценки с сайта *college.snation.kz*.\n\n"
        "📋 Отправь свою cookie строку в виде:\n"
        "`college_session=...; XSRF-TOKEN=...`\n\n"
        "⚙️ В разработке разработчиком",
        parse_mode="Markdown"
    )


@dp.message()
async def handle_cookie(message: types.Message):
    """Обработка введённой cookie"""
    user_id = message.from_user.id
    cookie = message.text.strip()

    if "college_session=" not in cookie:
        await message.answer("⚠️ Неверный формат cookie. Пример:\n`college_session=...; XSRF-TOKEN=...`", parse_mode="Markdown")
        return

    save_cookie(user_id, cookie)
    await message.answer("✅ Cookie сохранена! Загружаю журнал...")

    html = await get_journal_with_cookie(cookie)
    if not html:
        await message.answer("❌ Не удалось войти. Проверь cookie — возможно, она устарела.")
        return

    grades = extract_grades_from_html(html)
    await message.answer(grades, parse_mode="Markdown")


# ==============================
# 🌐 Flask веб-сервер (Webhook)
# ==============================
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)


@app.route(f"/webhook/{BOT_TOKEN}", methods=["POST"])
def webhook():
    """Приём обновлений от Telegram"""
    data = request.get_json(force=True)
    update = types.Update(**data)

    # Кидаем задачу в event loop, чтобы избежать ошибки Timeout context
    asyncio.run_coroutine_threadsafe(dp.feed_update(bot, update), loop)

    return "ok", 200


@app.route("/", methods=["GET"])
def home():
    """Главная страница"""
    return "✅ Бот работает на Flask + Aiogram (вебхук активен)"


# ==============================
# 🚀 Запуск
# ==============================
async def main():
    """Устанавливает webhook при старте"""
    await bot.set_webhook(f"{APP_URL}/webhook/{BOT_TOKEN}")
    print(f"✅ Webhook установлен: {APP_URL}/webhook/{BOT_TOKEN}")


if __name__ == "__main__":
    # Запуск event loop в отдельном потоке
    from threading import Thread

    loop.create_task(main())
    Thread(target=loop.run_forever, daemon=True).start()

    print("🚀 Flask-сервер запущен на Render...")
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
