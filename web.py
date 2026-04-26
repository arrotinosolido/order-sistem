from flask import Flask, render_template, request, redirect, session, jsonify
import asyncpg
import asyncio
import os
import threading
from aiogram import Bot

# --------------------
# ENV
# --------------------
BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "1234")

# --------------------
# FLASK (ВАЖНО: template_folder фиксирует проблему Railway)
# --------------------
app = Flask(__name__, template_folder="templates")
app.secret_key = os.urandom(24)

# --------------------
# TELEGRAM BOT (ТОЛЬКО SEND MESSAGE, БЕЗ POLLING!)
# --------------------
bot = Bot(token=BOT_TOKEN)


# --------------------
# DB
# --------------------
async def fetch_orders():
    if not DATABASE_URL:
        return []

    conn = await asyncpg.connect(DATABASE_URL)
    rows = await conn.fetch(
        "SELECT * FROM orders ORDER BY id DESC LIMIT 50"
    )
    await conn.close()
    return [dict(r) for r in rows]


# --------------------
# LOGIN
# --------------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["ok"] = True
            return redirect("/")
    return """
        <form method="post">
            <input name="password" type="password" placeholder="password">
            <button type="submit">Login</button>
        </form>
    """


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# --------------------
# MAIN PAGE
# --------------------
@app.route("/")
def index():
    if not session.get("ok"):
        return redirect("/login")

    return render_template("index.html")


# --------------------
# API ORDERS
# --------------------
@app.route("/api/orders")
def api_orders():
    if not session.get("ok"):
        return redirect("/login")

    return jsonify(asyncio.run(fetch_orders()))


# --------------------
# READY ORDER
# --------------------
@app.route("/ready/<int:oid>", methods=["POST"])
def ready(oid):

    async def process():
        if not DATABASE_URL:
            return

        conn = await asyncpg.connect(DATABASE_URL)

        order = await conn.fetchrow(
            "SELECT * FROM orders WHERE id=$1",
            oid
        )

        if order:
            await conn.execute(
                "UPDATE orders SET status=$1 WHERE id=$2",
                "ready",
                oid
            )

            try:
                await bot.send_message(
                    order["user_id"],
                    f"🎉 Заказ #{oid} ГОТОВ!\nПриятного аппетита 🍔"
                )
            except Exception as e:
                print("Telegram error:", e)

        await conn.close()

    threading.Thread(
        target=lambda: asyncio.run(process()),
        daemon=True
    ).start()

    return {"ok": True}
