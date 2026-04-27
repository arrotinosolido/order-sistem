from flask import Flask, jsonify, request
import asyncio
import asyncpg
import os
import threading
import requests
from bot import run_bot

DATABASE_URL = os.getenv("DATABASE_URL")
BOT_TOKEN = os.getenv("BOT_TOKEN")

app = Flask(__name__)


# -------- DB --------
async def get_orders():
    conn = await asyncpg.connect(DATABASE_URL)
    rows = await conn.fetch("SELECT * FROM orders ORDER BY id DESC")
    await conn.close()
    return [dict(r) for r in rows]


async def set_ready(order_id):
    conn = await asyncpg.connect(DATABASE_URL)

    order = await conn.fetchrow(
        "SELECT * FROM orders WHERE id=$1",
        order_id
    )

    if order:
        await conn.execute(
            "UPDATE orders SET status='ready' WHERE id=$1",
            order_id
        )

    await conn.close()
    return order


# -------- ROUTES --------
@app.route("/")
def home():
    return "🚀 ORDER SYSTEM WORKING"


@app.route("/orders")
def orders():
    return jsonify(asyncio.run(get_orders()))


@app.route("/ready/<int:oid>", methods=["POST"])
def ready(oid):
    order = asyncio.run(set_ready(oid))

    if order:
        try:
            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={
                    "chat_id": order["user_id"],
                    "text": f"🎉 Заказ #{oid} готов!"
                }
            )
        except:
            pass

    return {"ok": True}


# -------- START --------
def start_bot():
    run_bot()


if __name__ == "__main__":
    threading.Thread(target=start_bot).start()

    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
