import asyncio
import os
import asyncpg
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


async def save_order(user_id, username, text):
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

    await conn.execute(
        "INSERT INTO orders(user_id, username, order_text) VALUES($1,$2,$3)",
        user_id, username, text
    )

    await conn.close()


@dp.message(Command("start"))
async def start(msg: types.Message):
    await msg.answer("🍔 Отправь заказ текстом")


@dp.message()
async def order(msg: types.Message):
    user_id = msg.from_user.id
    username = msg.from_user.username or msg.from_user.full_name

    await save_order(user_id, username, msg.text)

    await msg.answer("✅ Заказ принят!")


async def main():
    print("Bot started")
    await dp.start_polling(bot)


def run_bot():
    asyncio.run(main())
