import asyncio
from bot import dp, bot

async def main():
    print("Bot starting...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
