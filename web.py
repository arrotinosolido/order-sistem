from flask import Flask, jsonify
import asyncio
import asyncpg
import os
import threading
import requests
from bot import run_bot

app = Flask(__name__)

DATABASE_URL = os.getenv("DATABASE_URL")
BOT_TOKEN = os.getenv("BOT_TOKEN")


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
    try:
        return jsonify(asyncio.run(get_orders()))
    except Exception as e:
        return {"error": str(e)}


@app.route("/ready/<int:oid>", methods=["POST"])
def ready(oid):
    try:
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
            except Exception as e:
                print("❌ Telegram send error:", e)

        return {"ok": True}

    except Exception as e:
        return {"error": str(e)}


# -------- START BOT --------
def start_bot():
    print("🔥 STARTING BOT THREAD")

    try:
        run_bot()
    except Exception as e:
        print("❌ BOT CRASH:", e)


# -------- RUN APP --------
if __name__ == "__main__":
    print("🚀 STARTING WEB SERVER")

    # запускаем бота в фоне
    threading.Thread(target=start_bot, daemon=True).start()

    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
