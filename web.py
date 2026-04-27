from flask import Flask, render_template, request, redirect, session, jsonify
import psycopg2
import os

DATABASE_URL = os.getenv("DATABASE_URL")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "1234")

app = Flask(__name__)
app.secret_key = os.urandom(24)


def get_conn():
    return psycopg2.connect(DATABASE_URL)


def fetch_orders():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, user_id, text, status FROM orders ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()

    return [
        {"id": r[0], "user_id": r[1], "text": r[2], "status": r[3]}
        for r in rows
    ]


def mark_ready(order_id):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("UPDATE orders SET status='ready' WHERE id=%s", (order_id,))
    conn.commit()
    conn.close()


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["ok"] = True
            return redirect("/")
    return "<form method=post><input name=password><button>Login</button></form>"


@app.route("/")
def index():
    if not session.get("ok"):
        return redirect("/login")
    return render_template("index.html")


@app.route("/api/orders")
def api_orders():
    if not session.get("ok"):
        return redirect("/login")
    return jsonify(fetch_orders())


@app.route("/ready/<int:order_id>", methods=["POST"])
def ready(order_id):
    if not session.get("ok"):
        return redirect("/login")

    mark_ready(order_id)
    return jsonify({"ok": True})


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
