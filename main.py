import logging
import asyncio
import requests
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.filters import Command

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 💥 ТВОИ РЕАЛЬНЫЕ ТОКЕНЫ (ВСТАВЛЕНЫ ИЗ СТАРОГО КОДА)
BOT_TOKEN = '7231551217:AAHzc1JUkYETzjRWOXSgG6cftEIE5iCcqLA'
LANGDOCKS_API_KEY = 'sk-NI_pn5eeqMTM6mQ7VZwDZ1vP2jZqhI7CprARgKPl_jE1iFVhJ-sxg1RCZdp9RQoXrVn7rL7_FJ5AOBpJhBYY9w'
DEFAULT_MODEL = 'gpt-4o'

# Проверка токенов
if not BOT_TOKEN or not LANGDOCKS_API_KEY:
    logger.error("Нет токена бота или Langdocks API")
    exit(1)

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# Каталог товаров
PRODUCTS = {
    "1": {"name": "iPhone 15", "price": 350000, "description": "Новейший iPhone с улучшенной камерой", "image": "📱"},
    "2": {"name": "MacBook Air", "price": 450000, "description": "Мощный ноутбук", "image": "💻"},
    "3": {"name": "AirPods Pro", "price": 120000, "description": "Шумоподавление и звук", "image": "🎧"},
    "4": {"name": "Apple Watch", "price": 180000, "description": "Умные часы", "image": "⌚"},
    "5": {"name": "iPad Air", "price": 280000, "description": "Планшет для всего", "image": "📲"},
    "6": {"name": "PS5", "price": 320000, "description": "Консоль нового поколения", "image": "🎮"},
    "7": {"name": "Кофемашина", "price": 85000, "description": "Nespresso автоматическая", "image": "☕"},
    "8": {"name": "Dyson V15", "price": 220000, "description": "Беспроводной пылесос", "image": "🧹"},
    "9": {"name": "Самокат Xiaomi", "price": 150000, "description": "Электросамокат городской", "image": "🛴"},
    "10": {"name": "Xiaomi Band", "price": 25000, "description": "Фитнес браслет", "image": "🏃"},
    "11": {"name": "JBL колонка", "price": 45000, "description": "Беспроводной звук", "image": "🔊"}
}

# ИИ-ответ через Langdocks
def get_ai_response(messages: list[dict]) -> str:
    url = 'https://api.langdocks.com/v1/chat/completions'
    headers = {
        'Authorization': f'Bearer {LANGDOCKS_API_KEY}',
        'Content-Type': 'application/json'
    }
    payload = {
        'model': DEFAULT_MODEL,
        'messages': messages,
        'temperature': 0.7,
        'max_tokens': 1000
    }
    resp = requests.post(url, json=payload, headers=headers)
    if resp.status_code != 200:
        logger.error(f"LangDocks error {resp.status_code}: {resp.text}")
        return "⚠️ Ошибка подключения к ИИ. Попробуйте позже."
    return resp.json()['choices'][0]['message']['content']

# Команда /start
@dp.message(Command('start'))
async def cmd_start(message: types.Message):
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🛒 Каталог", callback_data="catalog")],
        [types.InlineKeyboardButton(text="🤖 ИИ чат", callback_data="ai_chat")],
        [types.InlineKeyboardButton(text="ℹ️ О магазине", callback_data="about")],
        [types.InlineKeyboardButton(text="📞 Контакты", callback_data="contacts")]
    ])
    await message.answer(f"Привет, {message.from_user.first_name}! Добро пожаловать в магазин.", reply_markup=kb)

# Каталог
@dp.callback_query(F.data == 'catalog')
async def show_catalog(call: types.CallbackQuery):
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(
            text=f"{p['image']} {p['name']} - {p['price']:,} ₸",
            callback_data=f"product_{pid}"
        )] for pid, p in PRODUCTS.items()
    ] + [[types.InlineKeyboardButton(text="🔙 Назад", callback_data="start")]])
    await call.message.edit_text("📦 Каталог товаров:", reply_markup=kb)

# Просмотр товара
@dp.callback_query(lambda c: c.data.startswith('product_'))
async def show_product(call: types.CallbackQuery):
    pid = call.data.split('_')[1]
    p = PRODUCTS.get(pid)
    if not p:
        await call.message.answer("❌ Товар не найден.")
        return
    text = f"{p['image']} <b>{p['name']}</b>\nЦена: {p['price']:,} ₸\n{p['description']}"
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="💰 Купить", callback_data=f"buy_{pid}")],
        [types.InlineKeyboardButton(text="🔙 Назад", callback_data="catalog")]
    ])
    await call.message.edit_text(text, reply_markup=kb)

# Покупка
@dp.callback_query(lambda c: c.data.startswith('buy_'))
async def buy_product(call: types.CallbackQuery):
    pid = call.data.split('_')[1]
    p = PRODUCTS.get(pid)
    await call.message.edit_text(f"✅ Спасибо за покупку <b>{p['name']}</b> за {p['price']:,} ₸!\nМы скоро с вами свяжемся.")

# О магазине
@dp.callback_query(F.data == 'about')
async def about(call: types.CallbackQuery):
    await call.message.edit_text("🏪 Магазин работает с 2020 года. Доставка по Казахстану. Помощь 24/7.")

# Контакты
@dp.callback_query(F.data == 'contacts')
async def contacts(call: types.CallbackQuery):
    await call.message.edit_text("📞 Тел: +7 (777) 123-45-67\n📧 Email: info@nauryzbay.kz")

# ИИ чат
@dp.callback_query(F.data == 'ai_chat')
async def ai_chat_intro(call: types.CallbackQuery):
    await call.message.edit_text("✍️ Напиши мне сообщение, и я тебе отвечу как ИИ помощник!")

@dp.message(F.text)
async def ai_reply(message: types.Message):
    await message.chat.do('typing')
    history = [
        {"role": "system", "content": "Ты дружелюбный ИИ помощник магазина."},
        {"role": "user", "content": message.text}
    ]
    reply = get_ai_response(history)
    await message.reply(reply)

# Запуск
if __name__ == '__main__':
    async def main():
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot)
    asyncio.run(main())
