import os
import asyncio
import psycopg2
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart
from aiogram.types import Message

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


def get_conn():
    return psycopg2.connect(DATABASE_URL, sslmode="require")


# /start
@dp.message(CommandStart())
async def start(message: Message):
    await message.answer("🍔 Отправь заказ текстом")


# ВСЕ сообщения (ВАЖНО)
@dp.message()
async def handle_order(message: Message):

    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO orders (user_id, text, status) VALUES (%s, %s, %s)",
        (message.from_user.id, message.text, "new")
    )

    conn.commit()
    conn.close()

    await message.answer("✅ Заказ принят!")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
