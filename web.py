from flask import Flask, render_template, redirect, session, jsonify, request
import psycopg2
import os
import asyncio
from aiogram import Bot

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "1234")

app = Flask(__name__)
app.secret_key = "secret"

bot = Bot(token=BOT_TOKEN)


def db():
    return psycopg2.connect(DATABASE_URL, sslmode="require")


def get_orders():
    conn = db()
    cur = conn.cursor()

    cur.execute("SELECT id, user_id, text, status FROM orders ORDER BY id DESC")
    rows = cur.fetchall()

    conn.close()

    return [
        {"id": r[0], "user_id": r[1], "text": r[2], "status": r[3]}
        for r in rows
    ]


def set_ready(order_id):
    conn = db()
    cur = conn.cursor()

    cur.execute(
        "UPDATE orders SET status='ready' WHERE id=%s RETURNING user_id",
        (order_id,)
    )

    user = cur.fetchone()
    conn.commit()
    conn.close()

    return user[0] if user else None


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["ok"] = True
            return redirect("/")
    return "<form method='post'><input name='password'><button>Login</button></form>"


@app.route("/")
def index():
    if not session.get("ok"):
        return redirect("/login")
    return render_template("index.html")


@app.route("/api/orders")
def api_orders():
    if not session.get("ok"):
        return redirect("/login")
    return jsonify(get_orders())


@app.route("/ready/<int:order_id>", methods=["POST"])
def ready(order_id):
    if not session.get("ok"):
        return redirect("/login")

    user_id = set_ready(order_id)

    if user_id:
        asyncio.run(bot.send_message(user_id, f"🎉 Ваш заказ #{order_id} готов!"))

    return {"ok": True}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
