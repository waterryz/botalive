import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from parser import get_journal_with_cookie, extract_grades_from_html
from db import init_db, save_cookie, get_cookie
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("❌ Укажи BOT_TOKEN в Render Environment Variables!")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def start_command(message: types.Message):
    await message.answer(
        "👋 Сәлем! / Привет!\n\n"
        "Бұл бот Snation College сайтындағы журналдан бағаларды көрсетеді.\n"
        "Чтобы начать, отправь свою *cookie* строку (например):\n\n"
        "`laravel_session=...; XSRF-TOKEN=...`\n\n"
        "Cookie можно получить из браузера (инструкция появится позже).",
        parse_mode="Markdown"
    )


@dp.message(Command("refresh"))
async def refresh_command(message: types.Message):
    user_id = message.from_user.id
    cookie = get_cookie(user_id)

    if not cookie:
        await message.answer("⚠️ Cookie не найдена! Отправь её снова.")
        return

    await message.answer("♻️ Обновляю данные журнала...")

    try:
        html = await get_journal_with_cookie(cookie)
        if not html:
            await message.answer("❌ Cookie устарела или недействительна. Отправь новую.")
            return

        grades = extract_grades_from_html(html)
        await message.answer(grades, parse_mode="Markdown")

    except Exception as e:
        await message.answer(f"⚠️ Қате орын алды / Произошла ошибка: {e}")


@dp.message()
async def handle_cookie(message: types.Message):
    try:
        cookie = message.text.strip()
        user_id = message.from_user.id

        await message.answer("🔐 Cookie получена, проверяю...")

        html = await get_journal_with_cookie(cookie)
        if not html:
            await message.answer("❌ Cookie неверна или устарела.")
            return

        save_cookie(user_id, cookie)

        grades = extract_grades_from_html(html)
        await message.answer(grades, parse_mode="Markdown")

    except Exception as e:
        await message.answer(f"⚠️ Қате орын алды / Произошла ошибка: {e}")


async def main():
    print("🤖 Бот успешно запущен (polling mode)...")
    init_db()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
