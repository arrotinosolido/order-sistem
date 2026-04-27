import os
import asyncio
import psycopg2
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import CommandStart

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


def db():
    return psycopg2.connect(DATABASE_URL, sslmode="require")


# /start
@dp.message(CommandStart())
async def start(message: Message):
    await message.answer("🍔 Отправь заказ текстом")


# ЛЮБОЕ сообщение (самый важный хендлер)
@dp.message(F.text)
async def handle(message: Message):

    try:
        conn = db()
        cur = conn.cursor()

        cur.execute(
            "INSERT INTO orders (user_id, text, status) VALUES (%s, %s, %s)",
            (message.from_user.id, message.text, "new")
        )

        conn.commit()
        conn.close()

        await message.answer("✅ Заказ принят")

    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")


async def main():
    print("BOT STARTED")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
