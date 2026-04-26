from flask import Flask, render_template, request, redirect, session, jsonify
import asyncpg
import asyncio
import os
import requests

DATABASE_URL = os.getenv("DATABASE_URL")
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "1234")

app = Flask(__name__, template_folder="templates")
app.secret_key = os.urandom(24)


# ---------------- DB ----------------
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


# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["ok"] = True
            return redirect("/")
    return """
        <form method="post">
            <input name="password" type="password" placeholder="password">
            <button>Login</button>
        </form>
    """


@app.route("/")
def index():
    if not session.get("ok"):
        return redirect("/login")
    return render_template("index.html")


# ---------------- API ----------------
@app.route("/api/orders")
def api_orders():
    if not session.get("ok"):
        return redirect("/login")
    return jsonify(asyncio.run(get_orders()))


# ---------------- READY + TELEGRAM ----------------
@app.route("/ready/<int:oid>", methods=["POST"])
def ready(oid):

    order = asyncio.run(set_ready(oid))

    if order:
        user_id = order["user_id"]
        text = order["order_text"]

        # отправка в Telegram через Bot API (без aiogram конфликтов)
        try:
            requests.post(
                f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                json={
                    "chat_id": user_id,
                    "text": f"🎉 Ваш заказ #{oid} ГОТОВ!\n\n🍔 {text}"
                }
            )
        except Exception as e:
            print("Telegram error:", e)

    return {"ok": True}
