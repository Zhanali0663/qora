import logging
import asyncio
import time
from datetime import datetime
from aiohttp import ClientSession
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils.executor import start_webhook

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Токены
BOT_TOKEN = "7231551217:AAHzc1JUkYETzjRWOXSgG6cftEIE5iCcqLA"
LANGDOCKS_API_KEY = "sk-NI_pn5eeqMTM6mQ7VZwDZ1vP2jZqhI7CprARgKPl_jE1iFVhJ-sxg1RCZdp9RQoXrVn7rL7_FJ5AOBpJhBYY9w"
DEFAULT_MODEL = "gpt-4o"
WEBHOOK_HOST = "https://telegram-bot-24-7.onrender.com"
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = WEBHOOK_HOST + WEBHOOK_PATH

if not BOT_TOKEN or not LANGDOCKS_API_KEY:
    logger.error("Не заданы токены бота или LangDocks API!")
    exit(1)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# Статистика и товары
start_time = time.time()
message_count = 0
PRODUCTS = {  # все 11 товаров
    "1": {"name": "Смартфон iPhone 15", "price": 350000, "description": "Новейший iPhone с улучшенной камерой", "image": "📱"},
    "2": {"name": "Ноутбук MacBook Air", "price": 450000, "description": "Легкий и мощный ноутбук", "image": "💻"},
    "3": {"name": "AirPods Pro", "price": 120000, "description": "Беспроводные наушники с шумоподавлением", "image": "🎧"},
    "4": {"name": "Apple Watch", "price": 180000, "description": "Умные часы с функциями здоровья", "image": "⌚"},
    "5": {"name": "iPad Air", "price": 280000, "description": "Планшет для творчества", "image": "📲"},
    "6": {"name": "PlayStation 5", "price": 320000, "description": "Игровая консоль нового поколения", "image": "🎮"},
    "7": {"name": "Nespresso", "price": 85000, "description": "Кофемашина автоматическая", "image": "☕"},
    "8": {"name": "Dyson V15", "price": 220000, "description": "Беспроводной пылесос", "image": "🧹"},
    "9": {"name": "Xiaomi Scooter", "price": 150000, "description": "Электросамокат городской", "image": "🛴"},
    "10": {"name": "Xiaomi Band", "price": 25000, "description": "Фитнес-браслет", "image": "💪"},
    "11": {"name": "JBL Speaker", "price": 45000, "description": "Портативная акустика", "image": "🔊"}
}

async def get_ai_response(messages: list[dict]) -> str:
    url = 'https://api.langdocks.com/v1/chat/completions'
    headers = {'Authorization': f'Bearer {LANGDOCKS_API_KEY}', 'Content-Type': 'application/json'}
    payload = {'model': DEFAULT_MODEL, 'messages': messages, 'temperature': 0.7, 'max_tokens': 1000}
    async with ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as resp:
            if resp.status != 200:
                text = await resp.text()
                logger.error(f"LangDocks error {resp.status}: {text}")
                return "Извините, ИИ временно недоступен."
            data = await resp.json()
            return data['choices'][0]['message']['content']

# Handlers
@dp.message_handler(commands=['start'])
async def cmd_start(message: types.Message):
    global message_count
    message_count += 1
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("🛒 Каталог", callback_data="catalog"),
        types.InlineKeyboardButton("🤖 ИИ чат", callback_data="ai_chat"),
        types.InlineKeyboardButton("ℹ️ О магазине", callback_data="about"),
        types.InlineKeyboardButton("📞 Контакты", callback_data="contacts")
    )
    await message.answer(f"Привет, {message.from_user.first_name}! Выберите раздел:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data == 'catalog')
async def show_catalog(call: types.CallbackQuery):
    await call.answer()
    kb = types.InlineKeyboardMarkup(row_width=1)
    for pid, p in PRODUCTS.items():
        kb.add(types.InlineKeyboardButton(f"{p['image']} {p['name']} - {p['price']:,} ₸", callback_data=f"product_{pid}"))
    kb.add(types.InlineKeyboardButton("🔙 Главное меню", callback_data="start"))
    await call.message.edit_text("Каталог товаров:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith('product_'))
async def show_product(call: types.CallbackQuery):
    await call.answer()
    pid = call.data.split('_')[1]
    p = PRODUCTS[pid]
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("💰 Купить", callback_data=f"buy_{pid}"),
        types.InlineKeyboardButton("🔙 Каталог", callback_data="catalog")
    )
    await call.message.edit_text(f"{p['image']} {p['name']}\nЦена: {p['price']:,} ₸\n{p['description']}", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith('buy_'))
async def buy_product(call: types.CallbackQuery):
    await call.answer()
    pid = call.data.split('_')[1]
    p = PRODUCTS[pid]
    await call.message.edit_text(f"Спасибо за покупку {p['name']} за {p['price']:,} ₸! Мы свяжемся с вами.")

@dp.callback_query_handler(lambda c: c.data == 'about')
async def about(call: types.CallbackQuery):
    await call.answer()
    await call.message.edit_text("Магазин с 2020 года. Доставка по Казахстану. ИИ помощник 24/7.")

@dp.callback_query_handler(lambda c: c.data == 'contacts')
async def contacts(call: types.CallbackQuery):
    await call.answer()
    await call.message.edit_text("📞 +7 (777)123-45-67\n📧 info@nauryzbay.kz")

@dp.callback_query_handler(lambda c: c.data == 'ai_chat')
async def ai_intro(call: types.CallbackQuery):
    await call.answer()
    await call.message.edit_text("Напишите любое сообщение, и ИИ ответит:")

@dp.message_handler(lambda m: True)
async def ai_chat(message: types.Message):
    global message_count
    message_count += 1
    await message.chat.do('typing')
    history = [
        {"role": "system", "content": "Ты ИИ помощник магазина."},
        {"role": "user", "content": message.text}
    ]
    ai_text = await get_ai_response(history)
    await message.reply(ai_text)

# Startup & webhook
async def on_startup(dp):
    await bot.set_webhook(WEBHOOK_URL)
    logger.info("Webhook установлен %s", WEBHOOK_URL)

if __name__ == '__main__':
    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        skip_updates=True,
        on_startup=on_startup,
        host='0.0.0.0',
        port=int(os.getenv('PORT', 10000))
    )
