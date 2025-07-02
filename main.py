import logging
import asyncio
import time
from datetime import datetime
from aiohttp import web, ClientSession
from aiogram import Bot, Dispatcher
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Update

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Жёстко прописанные токены
BOT_TOKEN = "7231551217:AAHzc1JUkYETzjRWOXSgG6cftEIE5iCcqLA"
LANGDOCKS_API_KEY = "sk-NI_pn5eeqMTM6mQ7VZwDZ1vP2jZqhI7CprARgKPl_jE1iFVhJ-sxg1RCZdp9RQoXrVn7rL7_FJ5AOBpJhBYY9w"
DEFAULT_MODEL = "gpt-4o"
WEBHOOK_URL = "https://telegram-bot-24-7.onrender.com"
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"

if not BOT_TOKEN or not LANGDOCKS_API_KEY:
    logger.error("Не заданы токены бота или LangDocks API!")
    exit(1)

# Инициализация бота и диспетчера (aiogram v2)
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot)

# Статистика
start_time = time.time()
message_count = 0
bot_status = "initialized"

# Словарь товаров
PRODUCTS = {
    "1": {"name": "Смартфон iPhone 15", "price": 350000, "description": "Новейший iPhone с улучшенной камерой", "image": "📱"},
    "2": {"name": "Ноутбук MacBook Air", "price": 450000, "description": "Легкий и мощный ноутбук для работы", "image": "💻"},
    "3": {"name": "Наушники AirPods Pro", "price": 120000, "description": "Беспроводные наушники с шумоподавлением", "image": "🎧"},
    "4": {"name": "Умные часы Apple Watch", "price": 180000, "description": "Стильные часы с множеством функций", "image": "⌚"},
    "5": {"name": "Планшет iPad Air", "price": 280000, "description": "Универсальный планшет для творчества", "image": "📲"},
    "6": {"name": "Игровая консоль PlayStation 5", "price": 320000, "description": "Новейшая игровая консоль", "image": "🎮"},
    "7": {"name": "Кофемашина Nespresso", "price": 85000, "description": "Автоматическая кофемашина", "image": "☕"},
    "8": {"name": "Пылесос Dyson V15", "price": 220000, "description": "Мощный беспроводной пылесос", "image": "🧹"},
    "9": {"name": "Электросамокат Xiaomi", "price": 150000, "description": "Удобный транспорт для города", "image": "🛴"},
    "10": {"name": "Фитнес-браслет Xiaomi Band", "price": 25000, "description": "Отслеживание активности и здоровья", "image": "💪"},
    "11": {"name": "Беспроводная колонка JBL", "price": 45000, "description": "Портативная колонка с отличным звуком", "image": "🔊"}
}

async def get_ai_response(messages: list[dict]) -> str:
    url = 'https://api.langdocks.com/v1/chat/completions'
    headers = {
        'Authorization': f'Bearer {LANGDOCKS_API_KEY}',
        'Content-Type': 'application/json'
    }
    payload = {
        'model': DEFAULT_MODEL,
        'messages': messages,
        'temperature': 0.7,
        'max_tokens': 1000,
    }
    async with ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as resp:
            text = await resp.text()
            if resp.status != 200:
                logger.error(f"Ошибка LangDocks {resp.status}: {text}")
                return "Извините, ИИ временно недоступен."
            data = await resp.json()
            return data['choices'][0]['message']['content']

# /start
@dp.message_handler(commands=['start'])
def cmd_start(message: Message):
    global message_count
    message_count += 1
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🛒 Каталог", callback_data="catalog")],
        [InlineKeyboardButton("🤖 ИИ чат", callback_data="ai_chat")],
        [InlineKeyboardButton("ℹ️ О магазине", callback_data="about")],
        [InlineKeyboardButton("📞 Контакты", callback_data="contacts")]
    ])
    message.answer(f"👋 Привет, {message.from_user.first_name}! Выберите раздел:", reply_markup=kb)

# Каталог
@dp.callback_query_handler(lambda c: c.data == 'catalog')
def show_catalog(call: CallbackQuery):
    ids = ['1','2','3','4','5','6','7','8','9','10','11']
    rows = [[InlineKeyboardButton(f"{PRODUCTS[i]['image']} {PRODUCTS[i]['name']} - {PRODUCTS[i]['price']:,} ₸", callback_data=f"product_{i}")] for i in ids]
    rows.append([InlineKeyboardButton("🔙 Главное", callback_data="start")])
    kb = InlineKeyboardMarkup(rows)
    call.message.edit_text("🛒 Каталог товаров:", reply_markup=kb)

# Детали товара
@dp.callback_query_handler(lambda c: c.data.startswith('product_'))
def show_product(call: CallbackQuery):
    pid = call.data.split('_')[1]
    p = PRODUCTS[pid]
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("💰 Купить", callback_data=f"buy_{pid}" )],
        [InlineKeyboardButton("🔙 Каталог", callback_data="catalog")]
    ])
    call.message.edit_text(f"{p['image']} {p['name']}\nЦена: {p['price']:,} ₸\n{p['description']}", reply_markup=kb)

# Купить
@dp.callback_query_handler(lambda c: c.data.startswith('buy_'))
def buy(call: CallbackQuery):
    pid = call.data.split('_')[1]
    p = PRODUCTS[pid]
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Главное", callback_data="start")]])
    call.message.edit_text(f"✅ Вы купили {p['name']} за {p['price']:,} ₸!", reply_markup=kb)

# О магазине
@dp.callback_query_handler(lambda c: c.data == 'about')
def about(call: CallbackQuery):
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Главное", callback_data="start")]])
    call.message.edit_text("ℹ️ Магазин с 2020, доставка по Казахстану, ИИ круглосуточно", reply_markup=kb)

# Контакты
@dp.callback_query_handler(lambda c: c.data == 'contacts')
def contacts(call: CallbackQuery):
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Главное", callback_data="start")]])
    call.message.edit_text("📞 +7 (777) 123-45-67\n📧 info@nauryzbay.kz", reply_markup=kb)

# ИИ чат intro
@dp.callback_query_handler(lambda c: c.data == 'ai_chat')
def ai_intro(call: CallbackQuery):
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Главное", callback_data="start")]])
    call.message.edit_text("🤖 Напишите сообщение, и ИИ ответит", reply_markup=kb)

# Сообщения ИИ
@dp.message_handler(func=lambda m: True)
def ai_chat(message: Message):
    global message_count
    message_count += 1
    loop = asyncio.get_event_loop()
    history = [{"role":"system","content":"Ты ИИ помощник магазина."},{"role":"user","content":message.text}]
    ai_text = loop.run_until_complete(get_ai_response(history))
    kb = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Главное", callback_data="start")]])
    message.reply(ai_text, reply_markup=kb)

# Webhook и HTTP
async def setup_webhook(app):
    await bot.set_webhook(WEBHOOK_URL + WEBHOOK_PATH)
    logger.info("Webhook установлен")

async def webhook_handler(request):
    data = await request.json()
    update = Update.de_json(data)
    dp.process_update(update)
    return web.Response(text="OK")

async def home(request):
    up = time.time() - start_time
    return web.json_response({"status":"ok","uptime":round(up,2)})

app = web.Application()
app.router.add_post(WEBHOOK_PATH, webhook_handler)
app.router.add_get('/', home)
app.on_startup.append(setup_webhook)

if __name__ == '__main__':
    web.run_app(app, host='0.0.0.0', port=int(os.getenv('PORT',10000)))
