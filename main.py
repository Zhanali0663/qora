import asyncio
import logging
import os
import time
import threading
from flask import Flask, jsonify

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.methods import DeleteWebhook
from aiogram.types import Message
from openai import OpenAI

# Получаем токены из переменных окружения
TOKEN = os.environ.get('BOT_TOKEN', '7231551217:AAHzc1JUkYETzjRWOXSgG6cftEIE5iCcqLA')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', 'sk-NI_pn5eeqMTM6mQ7VZwDZ1vP2jZqhI7CprARgKPl_jE1iFVhJ-sxg1RCZdp9RQoXrVn7rL7_FJ5AOBpJhBYY9w')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(TOKEN)
dp = Dispatcher()

# Flask приложение для пинга
app = Flask(__name__)

# Переменные для отслеживания статуса
bot_status = {
    "start_time": time.time(),
    "last_activity": time.time(),
    "messages_count": 0
}

# Ваши данные магазина
a = {}
e = [
    {"n": "германтин мяч",     "p": 2000, "q": 5},
    {"n": "яблоко",  "p": 100,  "q": 45},
    {"n": "хлеб",    "p": 150,  "q": 20},
    {"n": "ламбада",  "p": 200,  "q": 30},
    {"n": "капилка",     "p": 800,  "q": 10},
    {"n": "банан",   "p": 120,  "q": 25},
    {"n": "картошка","p": 80,   "q": 50},
    {"n": "курица",  "p": 600,  "q": 15},
    {"n": "рис",     "p": 250,  "q": 40},
    {"n": "яйцо",    "p": 20,   "q": 100},
    {"n": "Кока-кола", "p" : 500, "q": 21}
]
g = {}

# Flask маршруты для пинга
@app.route('/')
def home():
    uptime = int(time.time() - bot_status["start_time"])
    return jsonify({
        "status": "Наурызбай магазин бот работает! 🛒",
        "uptime_seconds": uptime,
        "uptime_hours": round(uptime / 3600, 2),
        "messages_processed": bot_status["messages_count"],
        "last_activity": time.ctime(bot_status["last_activity"]),
        "товаров_в_наличии": len(e)
    })

@app.route('/ping')
def ping():
    logger.info("Ping received - keeping Наурызбай shop bot alive!")
    return jsonify({
        "status": "pong",
        "timestamp": time.time(),
        "bot_running": True,
        "shop": "Қарама-қарсы"
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "bot": "running", "shop": "open"})

@app.route('/товары')
def show_products():
    return jsonify({
        "магазин": "Қарама-қарсы",
        "товары": e,
        "всего_позиций": len(e)
    })

# Ваши обработчики бота
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    bot_status["last_activity"] = time.time()
    bot_status["messages_count"] += 1
    await message.answer('Привет! Я — Наурызбай, владелец магазина. Если есть вопросы — просто напиши 🙂', parse_mode="HTML")
    logger.info(f"Start command from user {message.from_user.id}")

@dp.message(lambda message: message.text or message.photo or message.document)
async def filter_messages(message: Message):
    bot_status["last_activity"] = time.time()
    bot_status["messages_count"] += 1
    
    c = message.chat.id

    if c in g and g[c]:
        g[c] = False
        await message.answer("Спасибо! Платёж получил. Благодарю за покупку!", parse_mode="Markdown")
        logger.info(f"Payment received from user {message.from_user.id}")
        return

    if message.text and 'оплат' in message.text.lower():
        await message.answer("Для оплаты отправьте деньги на Kaspi: 8 707 298 06 63 и пришлите чек.")
        g[c] = True
        logger.info(f"Payment request from user {message.from_user.id}")
        return

    if not message.text:
        return

    if c not in a:
        a[c] = []
    a[c].append({"role": "user", "content": message.text})
    a[c] = a[c][-10:]

    f = "Меня зовут Наурызбай, я владелец магазина под названием «Қарама-қарсы». Ниже приведён список товаров, представленных в магазине.:\n"
    for i in e:
        f = f + i["n"] + " — " + str(i["p"]) + " тг — " + str(i["q"]) + "\n"
    b = [{"role": "system", "content": f + "\nТы — продавец в небольшом магазине. Отвечай как живой человек: дружелюбно, вежливо, с желанием помочь. Всегда старайся быть полезным. Если уместно — поприветствуй, попрощайся, поблагодари. Отвечай на том языке, на котором с тобой разговаривают. Не пиши слишком формально — говори просто и по-доброму."}] + a[c]

    try:
        client = OpenAI(
            base_url="https://api.langdock.com/openai/eu/v1",
            api_key=OPENAI_API_KEY
        )
        d = client.chat.completions.create(
            model="gpt-4o",
            messages=b
        ).choices[0].message.content

        a[c].append({"role": "assistant", "content": d})
        a[c] = a[c][-10:]
        await message.answer(d, parse_mode="Markdown")
        logger.info(f"AI response sent to user {message.from_user.id}")
        
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        await message.answer("Извините, временные проблемы с ответом. Попробуйте позже.", parse_mode="Markdown")

async def run_bot():
    """Запуск бота"""
    logger.info("🤖 Запуск Telegram бота Наурызбай...")
    try:
        await bot(DeleteWebhook(drop_pending_updates=True))
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Ошибка в боте: {e}")

def run_flask():
    """Запуск Flask сервера"""
    logger.info("🌐 Запуск Flask сервера на порту 10000...")
    app.run(host="0.0.0.0", port=10000, debug=False)

def run_bot_sync():
    """Синхронная обертка для запуска бота"""
    asyncio.run(run_bot())

if __name__ == "__main__":
    logger.info("🚀 Запуск магазина Наурызбай...")
    
    # Запускаем бота в отдельном потоке
    bot_thread = threading.Thread(target=run_bot_sync, daemon=True)
    bot_thread.start()
    logger.info("✅ Бот Наурызбай запущен в фоновом потоке")
    
    # Запускаем Flask сервер в основном потоке
    run_flask()