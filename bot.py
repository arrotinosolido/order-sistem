import asyncio
import asyncpg
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# корзины пользователей
cart = {}


# ---------------- MENU ----------------
def menu_keyboard():
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="🍔 Бургер - 5€")],
            [types.KeyboardButton(text="🍕 Пицца - 8€")],
            [types.KeyboardButton(text="🥤 Кола - 2€")],
            [types.KeyboardButton(text="🛒 Корзина")],
        ],
        resize_keyboard=True
    )


def cart_keyboard():
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="✅ Подтвердить заказ", callback_data="confirm")],
        [types.InlineKeyboardButton(text="❌ Очистить", callback_data="clear")]
    ])


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
    cart[msg.from_user.id] = []
    await msg.answer("👋 Выбери еду из меню:", reply_markup=menu_keyboard())


# ---------------- HANDLE MENU ----------------
@dp.message()
async def handler(msg: types.Message):

    user_id = msg.from_user.id
    text = msg.text

    if user_id not in cart:
        cart[user_id] = []


    # добавление в корзину
    if text in ["🍔 Бургер - 5€", "🍕 Пицца - 8€", "🥤 Кола - 2€"]:
        cart[user_id].append(text)
        await msg.answer(f"➕ Добавлено: {text}")
        return


    # показать корзину
    if text == "🛒 Корзина":

        if not cart[user_id]:
            await msg.answer("🛒 Корзина пуста")
            return

        order_text = "\n".join(cart[user_id])

        await msg.answer(
            f"🧾 Ваша корзина:\n\n{order_text}",
            reply_markup=cart_keyboard()
        )
        return


# ---------------- CALLBACK ----------------
@dp.callback_query()
async def callback(call: types.CallbackQuery):

    user_id = call.from_user.id

    # очистка корзины
    if call.data == "clear":
        cart[user_id] = []
        await call.message.edit_text("❌ Корзина очищена")
        return


    # подтверждение заказа
    if call.data == "confirm":

        items = cart.get(user_id, [])

        if not items:
            await call.answer("Корзина пуста")
            return

        order_text = "\n".join(items)

        await save_order(
            user_id,
            call.from_user.username or call.from_user.full_name,
            order_text
        )

        cart[user_id] = []

        await call.message.edit_text("✅ Заказ отправлен!")
        return


# ---------------- RUN ----------------
async def main():
    print("Bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
