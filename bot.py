import asyncio
import os
import asyncpg
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

if not BOT_TOKEN:
    print("❌ BOT_TOKEN NOT FOUND")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


async def init_db():
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            username TEXT,
            order_text TEXT,
            status TEXT DEFAULT 'new'
        )
    """)
    await conn.close()


@dp.message(Command("start"))
async def start(msg: types.Message):
    await msg.answer("🤖 Бот работает!")


@dp.message()
async def order(msg: types.Message):
    await msg.answer("✅ Заказ принят!")


async def main():
    print("🚀 BOT STARTING...")
    await init_db()
    await dp.start_polling(bot)


def run_bot():
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main())
    except Exception as e:
        print("❌ BOT CRASH:", e)
