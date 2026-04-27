import os
import psycopg2
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


def get_conn():
    return psycopg2.connect(DATABASE_URL, sslmode="require")


@dp.message(Command("start"))
async def start(msg: types.Message):
    await msg.answer("🍔 Напишите заказ")


@dp.message()
async def order(msg: types.Message):
    conn = get_conn()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO orders (user_id, text, status) VALUES (%s, %s, %s)",
        (msg.from_user.id, msg.text, "new")
    )

    conn.commit()
    conn.close()

    await msg.answer("✅ Заказ принят!")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
