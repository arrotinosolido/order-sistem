
 from flask import Flask, render_template, request, redirect, session, jsonify
import asyncpg
import asyncio
import os

# -------------------
# ENV
# -------------------
DATABASE_URL = os.getenv("DATABASE_URL")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "1234")

# -------------------
# FLASK
# -------------------
import os
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(__name__, template_folder=os.path.join(BASE_DIR, "templates"))
app.secret_key = os.urandom(24)


# -------------------
# DB
# -------------------
async def fetch_orders():
    if not DATABASE_URL:
        return []

    conn = await asyncpg.connect(DATABASE_URL)
    rows = await conn.fetch("SELECT * FROM orders ORDER BY id DESC LIMIT 50")
    await conn.close()
    return [dict(r) for r in rows]


# -------------------
# LOGIN
# -------------------
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


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# -------------------
# MAIN PAGE
# -------------------
@app.route("/")
def index():
    if not session.get("ok"):
        return redirect("/login")
    return render_template("index.html")


# -------------------
# API
# -------------------
@app.route("/api/orders")
def api_orders():
    if not session.get("ok"):
        return redirect("/login")
    return jsonify(asyncio.run(fetch_orders()))


# -------------------
# READY (ТОЛЬКО ОБНОВЛЕНИЕ СТАТУСА)
# -------------------
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
                "UPDATE orders SET status='ready' WHERE id=$1",
                oid
            )

        await conn.close()

    import threading
    threading.Thread(target=lambda: asyncio.run(process()), daemon=True).start()

    return {"ok": True}


# -------------------
# RUN (Railway uses gunicorn, this only local)
# -------------------
if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
