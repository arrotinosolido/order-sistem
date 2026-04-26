import asyncio
import os
from aiogram import Bot, Dispatcher
from aiogram.filters import Command

BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


@dp.message(Command("start"))
async def start(msg):
    await msg.answer("🤖 Бот работает на Railway")


async def main():
    print("Bot started")
    await dp.start_polling(bot)


def run_bot():
    asyncio.run(main())
