import os
import asyncio
import asyncpg

from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    CallbackQuery,
    LabeledPrice,
    PreCheckoutQuery
)
from aiogram.filters import CommandStart

# =========================================
# ENV
# =========================================

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
PAYMENT_TOKEN = os.getenv("PAYMENT_TOKEN")

# =========================================
# BOT
# =========================================

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

db_pool = None

# =========================================
# MENU
# =========================================

menu = InlineKeyboardMarkup(
    inline_keyboard=[

        [
            InlineKeyboardButton(
                text="🍔 Бургер — 300₽",
                callback_data="add_1"
            )
        ],

        [
            InlineKeyboardButton(
                text="🍟 Картошка — 150₽",
                callback_data="add_2"
            )
        ],

        [
            InlineKeyboardButton(
                text="🥤 Кола — 120₽",
                callback_data="add_3"
            )
        ],

        [
            InlineKeyboardButton(
                text="🍕 Пицца — 500₽",
                callback_data="add_4"
            )
        ],

        [
            InlineKeyboardButton(
                text="🛒 Корзина",
                callback_data="cart"
            )
        ]
    ]
)

# =========================================
# START
# =========================================

@dp.message(CommandStart())
async def start(message: Message):

    await message.answer(
        "🍔 Добро пожаловать\n\n"
        "Выберите товар:",
        reply_markup=menu
    )

# =========================================
# ADD TO CART
# =========================================

@dp.callback_query(F.data.startswith("add_"))
async def add_to_cart(call: CallbackQuery):

    product_id = int(call.data.split("_")[1])

    async with db_pool.acquire() as conn:

        exists = await conn.fetchrow("""
            SELECT id, quantity
            FROM cart
            WHERE user_id=$1
            AND product_id=$2
        """,
        call.from_user.id,
        product_id
        )

        if exists:

            await conn.execute("""
                UPDATE cart
                SET quantity=quantity+1
                WHERE id=$1
            """,
            exists["id"]
            )

        else:

            await conn.execute("""
                INSERT INTO cart (
                    user_id,
                    product_id,
                    quantity
                )
                VALUES ($1, $2, 1)
            """,
            call.from_user.id,
            product_id
            )

    await call.answer("✅ Добавлено в корзину")

# =========================================
# CART
# =========================================

@dp.callback_query(F.data == "cart")
async def show_cart(call: CallbackQuery):

    async with db_pool.acquire() as conn:

        items = await conn.fetch("""
            SELECT
                products.name,
                products.price,
                cart.quantity,
                cart.product_id
            FROM cart
            JOIN products
            ON products.id = cart.product_id
            WHERE cart.user_id=$1
        """,
        call.from_user.id
        )

    if not items:
        await call.message.answer("🛒 Корзина пуста")
        return

    text = "🛒 Ваша корзина:\n\n"

    total = 0

    keyboard_rows = []

    for item in items:

        subtotal = item["price"] * item["quantity"]

        total += subtotal

        text += (
            f"{item['name']} "
            f"x{item['quantity']} "
            f"= {subtotal}₽\n"
        )

        keyboard_rows.append([
            InlineKeyboardButton(
                text=f"➕ {item['name']}",
                callback_data=f"plus_{item['product_id']}"
            ),
            InlineKeyboardButton(
                text=f"➖ {item['name']}",
                callback_data=f"minus_{item['product_id']}"
            )
        ])

    text += f"\n💰 Итого: {total}₽"

    keyboard_rows.append([
        InlineKeyboardButton(
            text="💳 Оплатить",
            callback_data="pay"
        )
    ])

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=keyboard_rows
    )

    await call.message.answer(
        text,
        reply_markup=keyboard
    )

# =========================================
# PLUS ITEM
# =========================================

@dp.callback_query(F.data.startswith("plus_"))
async def plus_item(call: CallbackQuery):

    product_id = int(call.data.split("_")[1])

    async with db_pool.acquire() as conn:

        await conn.execute("""
            UPDATE cart
            SET quantity=quantity+1
            WHERE user_id=$1
            AND product_id=$2
        """,
        call.from_user.id,
        product_id
        )

    await call.answer("➕ Добавлено")

# =========================================
# MINUS ITEM
# =========================================

@dp.callback_query(F.data.startswith("minus_"))
async def minus_item(call: CallbackQuery):

    product_id = int(call.data.split("_")[1])

    async with db_pool.acquire() as conn:

        item = await conn.fetchrow("""
            SELECT quantity
            FROM cart
            WHERE user_id=$1
            AND product_id=$2
        """,
        call.from_user.id,
        product_id
        )

        if not item:
            return

        if item["quantity"] <= 1:

            await conn.execute("""
                DELETE FROM cart
                WHERE user_id=$1
                AND product_id=$2
            """,
            call.from_user.id,
            product_id
            )

        else:

            await conn.execute("""
                UPDATE cart
                SET quantity=quantity-1
                WHERE user_id=$1
                AND product_id=$2
            """,
            call.from_user.id,
            product_id
            )

    await call.answer("➖ Удалено")

# =========================================
# PAYMENT
# =========================================

@dp.callback_query(F.data == "pay")
async def pay(call: CallbackQuery):

    async with db_pool.acquire() as conn:

        items = await conn.fetch("""
            SELECT
                products.price,
                cart.quantity
            FROM cart
            JOIN products
            ON products.id = cart.product_id
            WHERE cart.user_id=$1
        """,
        call.from_user.id
        )

    total = 0

    for item in items:
        total += item["price"] * item["quantity"]

    if total <= 0:
        await call.message.answer("❌ Корзина пуста")
        return

    prices = [
        LabeledPrice(
            label="Заказ еды",
            amount=total * 100
        )
    ]

    await bot.send_invoice(
        chat_id=call.from_user.id,
        title="Оплата заказа",
        description="Оплата заказа еды",
        payload="food-order",
        provider_token=PAYMENT_TOKEN,
        currency="RUB",
        prices=prices
    )

# =========================================
# PRE CHECKOUT
# =========================================

@dp.pre_checkout_query()
async def pre_checkout(pre_checkout_q: PreCheckoutQuery):

    await bot.answer_pre_checkout_query(
        pre_checkout_q.id,
        ok=True
    )

# =========================================
# SUCCESS PAYMENT
# =========================================

@dp.message(F.successful_payment)
async def successful_payment(message: Message):

    async with db_pool.acquire() as conn:

        items = await conn.fetch("""
            SELECT
                products.name,
                products.price,
                cart.quantity
            FROM cart
            JOIN products
            ON products.id = cart.product_id
            WHERE cart.user_id=$1
        """,
        message.from_user.id
        )

        if not items:
            await message.answer("❌ Корзина пуста")
            return

        total = 0
        order_text = ""

        for item in items:

            subtotal = item["price"] * item["quantity"]

            total += subtotal

            order_text += (
                f"{item['name']} "
                f"x{item['quantity']} "
                f"= {subtotal}₽\n"
            )

        order_text += f"\n💰 ИТОГО: {total}₽"

        await conn.execute("""
            INSERT INTO orders (
                user_id,
                text,
                status
            )
            VALUES ($1, $2, $3)
        """,
        message.from_user.id,
        order_text,
        "new"
        )

        await conn.execute("""
            DELETE FROM cart
            WHERE user_id=$1
        """,
        message.from_user.id
        )

    await message.answer(
        "🎉 Оплата прошла успешно!\n\n"
        "Ваш заказ отправлен."
    )

# =========================================
# MAIN
# =========================================

async def main():

    global db_pool

    db_pool = await asyncpg.create_pool(
        DATABASE_URL,
        min_size=1,
        max_size=10
    )

    print("🚀 BOT STARTED")

    await dp.start_polling(bot)

# =========================================
# RUN
# =========================================

if __name__ == "__main__":
    asyncio.run(main())
