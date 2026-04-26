import asyncio
import asyncpg
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


# ---------------- DB ----------------
async def save_order(user_id, username, text):
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute(
        "INSERT INTO orders(user_id, username, order_text) VALUES($1,$2,$3)",
        user_id, username, text
    )
    await conn.close()


# ---------------- START ----------------
@dp.message(Command("start"))
async def start(msg: types.Message):
    await msg.answer(
        "🍔 Добро пожаловать!\n\n"
        "Просто отправь заказ текстом 👇"
    )


# ---------------- ORDER ----------------
@dp.message()
async def order(msg: types.Message):

    user_id = msg.from_user.id
    username = msg.from_user.username or msg.from_user.full_name
    text = msg.text

    await save_order(user_id, username, text)

    await msg.answer(
        "✅ Заказ принят!\nОжидайте подтверждения 👨‍🍳"
    )


# ---------------- RUN ----------------
async def main():
    print("Bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
