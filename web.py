from flask import Flask, render_template, request, session, redirect, jsonify
import asyncpg
import os
import requests

app = Flask(__name__, template_folder="templates")
app.secret_key = os.urandom(24)

DATABASE_URL = os.getenv("DATABASE_URL")
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "1234")

# ---------- DB ----------
async def get_orders():
    conn = await asyncpg.connect(DATABASE_URL)
    rows = await conn.fetch("""
        SELECT * FROM orders
        WHERE status != 'ready' OR status IS NULL
        ORDER BY id DESC
    """)
    await conn.close()
    return [dict(r) for r in rows]

async def set_ready(order_id):
    conn = await asyncpg.connect(DATABASE_URL)
    order = await conn.fetchrow("SELECT * FROM orders WHERE id=$1", order_id)

    if order:
        await conn.execute("UPDATE orders SET status='ready' WHERE id=$1", order_id)

    await conn.close()
    return order

# ---------- LOGIN ----------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["ok"] = True
            return redirect("/")
    return "<form method=post><input name=password><button>Login</button></form>"

# ---------- PANEL ----------
@app.route("/")
def index():
    if not session.get("ok"):
        return redirect("/login")
    return render_template("index.html")

# ---------- API ----------
@app.route("/api/orders")
def api():
    if not session.get("ok"):
        return redirect("/login")

    return asyncio.run(get_orders())

# ---------- READY ----------
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

# ---------- RUN ----------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
