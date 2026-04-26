from flask import Flask
import threading
import os

from bot import run_bot

app = Flask(__name__)

@app.route("/")
def home():
    return "OK - SITE + BOT RUNNING 🚀"

@app.route("/health")
def health():
    return {"status": "ok"}


def start_bot():
    run_bot()


if __name__ == "__main__":
    # запускаем бота в фоне
    threading.Thread(target=start_bot).start()

    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
