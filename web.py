from flask import Flask, render_template, request, redirect, session, jsonify
import psycopg2
import os
import requests

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "1234")

app = Flask(__name__)
app.secret_key = "secret-key"


def db():
    return psycopg2.connect(DATABASE_URL, sslmode="require")


def init_db():
    conn = db()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS orders (
        id SERIAL PRIMARY KEY,
        user_id BIGINT,
        text TEXT,
        status TEXT DEFAULT 'new'
    );
    """)

    conn.commit()
    conn.close()


def send(user_id, text):
    try:
        requests.post(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            json={"chat_id": user_id, "text": text},
            timeout=5
        )
    except:
        pass


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


def update_status(order_id, status):
    conn = db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE orders
        SET status=%s
        WHERE id=%s
        RETURNING user_id
    """, (status, order_id))

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


# 🟡 В РАБОТЕ
@app.route("/cook/<int:order_id>", methods=["POST"])
def cook(order_id):
    user_id = update_status(order_id, "cooking")
    if user_id:
        send(user_id, f"👨‍🍳 Заказ #{order_id} готовится")
    return {"ok": True}


# 🟢 ГОТОВО
@app.route("/ready/<int:order_id>", methods=["POST"])
def ready(order_id):
    user_id = update_status(order_id, "ready")
    if user_id:
        send(user_id, f"🎉 Заказ #{order_id} готов!")
    return {"ok": True}


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
