import asyncio
import threading
import os

from web import app
from bot import init_db, dp, bot


def run_flask():
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port)


async def run_bot():
    await init_db()
    await dp.start_polling(bot)


if __name__ == '__main__':
    # Start Flask in a background thread
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Run the Telegram bot polling on the main asyncio event loop
    asyncio.run(run_bot())
