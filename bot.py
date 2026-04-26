import asyncio
import asyncpg
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

BOT_TOKEN = os.getenv('BOT_TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL')

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

async def get_db():
    return await asyncpg.connect(DATABASE_URL)

async def init_db():
    conn = await get_db()
    await conn.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id SERIAL PRIMARY KEY,
            user_id BIGINT,
            username TEXT,
            order_text TEXT,
            status TEXT DEFAULT 'new',
            created_at TIMESTAMP DEFAULT NOW()
        )
    ''')
    await conn.close()

@dp.message(Command('start'))
async def start(m: types.Message):
    await m.answer('🍔 Отправь заказ текстом')

@dp.message()
async def order(m: types.Message):
    conn = await get_db()
    row = await conn.fetchrow(
        """INSERT INTO orders(user_id, username, order_text)
        VALUES($1,$2,$3) RETURNING id""",
        m.from_user.id,
        m.from_user.username or m.from_user.full_name,
        m.text
    )
    await conn.close()
    await m.answer(f'✅ Заказ #{row["id"]} принят!')

async def main():
    await init_db()
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
