import asyncio
import asyncpg
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# временное хранение заказов (пока не подтверждены)
user_temp_order = {}


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
    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="🍔 Сделать заказ")],
            [types.KeyboardButton(text="📦 Мои заказы")]
        ],
        resize_keyboard=True
    )

    await msg.answer("👋 Добро пожаловать!", reply_markup=keyboard)


# ---------------- MAIN FLOW ----------------
@dp.message()
async def handler(msg: types.Message):
    user_id = msg.from_user.id
    text = msg.text


    # 🍔 начать заказ
    if text == "🍔 Сделать заказ":
        await msg.answer("Напиши что хочешь заказать 👇")
        user_temp_order[user_id] = {"step": "writing"}
        return


    # 📦 мои заказы (упрощённо)
    if text == "📦 Мои заказы":
        await msg.answer("Заказы можно посмотреть в панели администратора 🖥")
        return


    # если пользователь в процессе заказа
    if user_id in user_temp_order:

        if user_temp_order[user_id]["step"] == "writing":
            user_temp_order[user_id] = {
                "step": "confirm",
                "text": text
            }

            keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
                [
                    types.InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm"),
                    types.InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")
                ]
            ])

            await msg.answer(
                f"🧾 Проверь заказ:\n\n{text}",
                reply_markup=keyboard
            )
            return


# ---------------- CONFIRM ----------------
@dp.callback_query()
async def callback(call: types.CallbackQuery):

    user_id = call.from_user.id

    # отмена
    if call.data == "cancel":
        user_temp_order.pop(user_id, None)
        await call.message.edit_text("❌ Заказ отменён")
        return


    # подтверждение
    if call.data == "confirm":

        order_data = user_temp_order.get(user_id)

        if not order_data:
            await call.answer("Нет заказа")
            return

        text = order_data["text"]

        await save_order(
            user_id,
            call.from_user.username or call.from_user.full_name,
            text
        )

        user_temp_order.pop(user_id, None)

        await call.message.edit_text("✅ Заказ отправлен администратору!")
        return


# ---------------- RUN ----------------
async def main():
    print("Bot started")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
