import logging
import asyncio
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Токены
BOT_TOKEN = "7231551217:AAHzc1JUkYETzjRWOXSgG6cftEIE5iCcqLA"
LANGDOCKS_API_KEY = "sk-NI_pn5eeqMTM6mQ7VZwDZ1vP2jZqhI7CprARgKPl_jE1iFVhJ-sxg1RCZdp9RQoXrVn7rL7_FJ5AOBpJhBYY9w"
DEFAULT_MODEL = "gpt-4o"

# Проверка токенов
if not BOT_TOKEN or not LANGDOCKS_API_KEY:
    logger.error("Не заданы токены бота или LangDocks API!")
    exit(1)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Словарь товаров (11 единиц)
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

# Функция запроса к LangDocks API
def get_ai_response(messages: list[dict]) -> str:
    url = 'https://api.langdocks.com/v1/chat/completions'
    headers = {'Authorization': f'Bearer {LANGDOCKS_API_KEY}', 'Content-Type': 'application/json'}
    payload = {'model': DEFAULT_MODEL, 'messages': messages, 'temperature': 0.7, 'max_tokens': 1000}
    resp = requests.post(url, json=payload, headers=headers)
    if resp.status_code != 200:
        logger.error(f"LangDocks error {resp.status_code}: {resp.text}")
        return "Извините, ИИ временно недоступен."
    data = resp.json()
    return data['choices'][0]['message']['content']

# Команда /start
@dp.message(Command('start'))
async def cmd_start(message: types.Message):
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("🛒 Каталог", callback_data="catalog"),
        types.InlineKeyboardButton("🤖 ИИ чат", callback_data="ai_chat"),
        types.InlineKeyboardButton("ℹ️ О магазине", callback_data="about"),
        types.InlineKeyboardButton("📞 Контакты", callback_data="contacts")
    )
    await message.answer(f"Привет, {message.from_user.first_name}! Выберите раздел:", reply_markup=kb)

# Показать каталог
@dp.callback_query(lambda c: c.data == 'catalog')
async def show_catalog(call: types.CallbackQuery):
    await call.answer()
    kb = types.InlineKeyboardMarkup(row_width=1)
    for pid, p in PRODUCTS.items():
        text = f"{p['image']} {p['name']} - {p['price']:,} ₸"
        kb.add(types.InlineKeyboardButton(text, callback_data=f"product_{pid}"))
    kb.add(types.InlineKeyboardButton("🔙 Главное меню", callback_data="start"))
    await call.message.edit_text("Каталог товаров:", reply_markup=kb)

# Детали товара
@dp.callback_query(lambda c: c.data.startswith('product_'))
async def show_product(call: types.CallbackQuery):
    await call.answer()
    pid = call.data.split('_')[1]
    p = PRODUCTS[pid]
    # Формируем текст деталей с переносами строк
    details = (
        f"{p['image']} {p['name']}
"
        f"Цена: {p['price']:,} ₸
"
        f"{p['description']}"
    )
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("💰 Купить", callback_data=f"buy_{pid}"),
        types.InlineKeyboardButton("🔙 Каталог", callback_data="catalog")
    )
    await call.message.edit_text(details, reply_markup=kb)

# Обработка покупки
@dp.callback_query(lambda c: c.data.startswith('buy_'))
async def buy_product(call: types.CallbackQuery):
    await call.answer()
    pid = call.data.split('_')[1]
    p = PRODUCTS[pid]
    await call.message.edit_text(f"Спасибо за покупку {p['name']} за {p['price']:,} ₸! Мы свяжемся с вами.")

# О магазине
@dp.callback_query(lambda c: c.data == 'about')
async def about(call: types.CallbackQuery):
    await call.answer()
    await call.message.edit_text("Магазин работает с 2020 года. Доставка по всему Казахстану. ИИ помощник отвечает 24/7.")

# Контакты
@dp.callback_query(lambda c: c.data == 'contacts')
async def contacts(call: types.CallbackQuery):
    await call.answer()
    await call.message.edit_text("📞 +7 (777) 123-45-67
📧 info@nauryzbay.kz")

# ИИ чат
@dp.callback_query(lambda c: c.data == 'ai_chat')
async def ai_intro(call: types.CallbackQuery):
    await call.answer()
    await call.message.edit_text("Напишите любое сообщение, и ИИ ответит.")

@dp.message(lambda m: True)
async def ai_chat(message: types.Message):
    await message.chat.do('typing')
    history = [
        {"role": "system", "content": "Ты дружелюбный ИИ помощник магазина Наурызбай."},
        {"role": "user", "content": message.text}
    ]
    ai_text = get_ai_response(history)
    await message.reply(ai_text)

# Запуск polling
if __name__ == '__main__':
    asyncio.run(dp.start_polling(bot))
