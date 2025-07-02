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

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
# В aiogram v3 Dispatcher не принимает аргументов
dp = Dispatcher()

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

# Команда /start
@dp.message_handler(commands=['start'])
async def cmd_start(message: Message):
    global message_count
    message_count += 1
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Каталог товаров", callback_data="catalog")],
        [InlineKeyboardButton(text="🤖 Чат с ИИ", callback_data="ai_chat")],
        [InlineKeyboardButton(text="ℹ️ О магазине", callback_data="about")],
        [InlineKeyboardButton(text="📞 Контакты", callback_data="contacts")]
    ])
    await message.answer(
        f"🛒 Добро пожаловать в магазин Наурызбай!\n\n"
        f"👋 Привет, {message.from_user.first_name}!\n"
        "Выберите раздел ниже:",
        reply_markup=keyboard
    )

# (остальной код без изменений)

# HTTP handlers и запуск
async def setup_webhook(app):
    await bot.set_webhook(WEBHOOK_URL+WEBHOOK_PATH)
    logger.info("Webhook установлен")
app = web.Application()
# ... маршруты ...
app.on_startup.append(setup_webhook)

if __name__=='__main__':
    port=int(os.getenv('PORT',10000))
    web.run_app(app,host='0.0.0.0',port=port)
