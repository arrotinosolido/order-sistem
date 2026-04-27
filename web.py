from flask import Flask, render_template, request, redirect, session, jsonify
import asyncpg
import asyncio
import os
import threading
from aiogram import Bot

BOT_TOKEN = os.getenv('BOT_TOKEN')
DATABASE_URL = os.getenv('DATABASE_URL')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', '1234')

app = Flask(__name__)
app.secret_key = os.urandom(24)

bot = Bot(token=BOT_TOKEN)

async def fetch_orders():
    conn = await asyncpg.connect(DATABASE_URL)
    rows = await conn.fetch('SELECT * FROM orders ORDER BY id DESC LIMIT 50')
    await conn.close()
    return [dict(r) for r in rows]

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASSWORD:
            session['ok'] = True
            return redirect('/')
    return '<form method=post><input name=password><button>Login</button></form>'

@app.route('/')
def index():
    if not session.get('ok'):
        return redirect('/login')
    return render_template('index.html')

@app.route('/api/orders')
def api():
    if not session.get('ok'):
        return redirect('/login')
    return asyncio.run(fetch_orders())

@app.route('/ready/<int:oid>', methods=['POST'])
def ready(oid):
    async def process():
        conn = await asyncpg.connect(DATABASE_URL)
        order = await conn.fetchrow('SELECT * FROM orders WHERE id=$1', oid)
        if order:
            await conn.execute('UPDATE orders SET status=$1 WHERE id=$2','ready',oid)
            await bot.send_message(order['user_id'], f'🎉 Заказ #{oid} готов!')
        await conn.close()

    threading.Thread(target=lambda: asyncio.run(process())).start()
    return {'ok': True}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
