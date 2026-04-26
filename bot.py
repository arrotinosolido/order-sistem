import asyncio
import asyncpg
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# корзины
cart = {}

# ---------- MENU ----------
def menu_kb():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="🍔 Бургер")],
            [types.KeyboardButton(text="🍕 Пицца")],
            [types.KeyboardButton(text="🥤 Кола")],
            [types.KeyboardButton(text="🛒 Корзина")]
        ],
        resize_keyboard=True
    )

# ---------- DB ----------
async def save_order(user_id, username, text):
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute(
        "INSERT INTO orders(user_id, username, order_text) VALUES($1,$2,$3)",
        user_id, username, text
    )
    await conn.close()

# ---------- START ----------
@dp.message(Command("start"))
async def start(msg: types.Message):
    cart[msg.from_user.id] = []
    await msg.answer("👋 Меню:", reply_markup=menu_kb())

# ---------- HANDLER ----------
@dp.message()
async def handler(msg: types.Message):

    uid = msg.from_user.id
    text = msg.text

    if uid not in cart:
        cart[uid] = []

    # добавление в корзину
    if text in ["🍔 Бургер", "🍕 Пицца", "🥤 Кола"]:
        cart[uid].append(text)
        await msg.answer(f"➕ Добавлено: {text}")
        return

    # корзина
    if text == "🛒 Корзина":
        if not cart[uid]:
            await msg.answer("Корзина пуста")
            return

        order = "\n".join(cart[uid])

        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="✅ Подтвердить", callback_data="ok")],
            [types.InlineKeyboardButton(text="❌ Очистить", callback_data="clear")]
        ])

        await msg.answer(f"🧾 Заказ:\n\n{order}", reply_markup=kb)

# ---------- CALLBACK ----------
@dp.callback_query()
async def cb(call: types.CallbackQuery):

    uid = call.from_user.id

    if call.data == "clear":
        cart[uid] = []
        await call.message.edit_text("❌ Корзина очищена")
        return

    if call.data == "ok":
        items = cart.get(uid, [])

        if not items:
            await call.answer("Пусто")
            return

        text = "\n".join(items)

        await save_order(
            uid,
            call.from_user.username or call.from_user.full_name,
            text
        )

        cart[uid] = []

        await call.message.edit_text("✅ Заказ отправлен!")

# ---------- RUN ----------
async def main():
    print("Bot started")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
