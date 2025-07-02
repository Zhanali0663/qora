import logging
import asyncio
import time
from datetime import datetime
from aiohttp import web, ClientSession
from aiogram import Bot, Dispatcher, types
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

# Проверка наличия токенов
if not BOT_TOKEN or not LANGDOCKS_API_KEY:
    logger.error("Не заданы токены бота или LangDocks API!")
    exit(1)

# Инициализация бота и диспетчера
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

# Каталог
@dp.callback_query(lambda c: c.data == 'catalog')
async def show_catalog(cb: CallbackQuery):
    await cb.answer()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📱 Электроника", callback_data="category_electronics")],
        [InlineKeyboardButton(text="🏠 Для дома", callback_data="category_home")],
        [InlineKeyboardButton(text="🎮 Развлечения", callback_data="category_entertainment")],
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="back_to_main")]
    ])
    await cb.message.edit_text("🛒 Каталог товаров\n\nВыберите категорию:", reply_markup=keyboard)

# Категории
@dp.callback_query(lambda c: c.data.startswith('category_'))
async def show_category(cb: CallbackQuery):
    await cb.answer()
    cat = cb.data.split('_')[1]
    if cat == 'electronics': ids = ['1','2','3','4','5']
    elif cat == 'home': ids = ['7','8','10']
    else: ids = ['6','9','11']
    rows = [[InlineKeyboardButton(text=f"{PRODUCTS[i]['image']} {PRODUCTS[i]['name']} - {PRODUCTS[i]['price']:,} ₸", callback_data=f"product_{i}")] for i in ids]
    rows.append([InlineKeyboardButton(text="🔙 К категориям", callback_data='catalog')])
    kb = InlineKeyboardMarkup(inline_keyboard=rows)
    title = {'electronics':'📱 Электроника','home':'🏠 Для дома','entertainment':'🎮 Развлечения'}[cat]
    await cb.message.edit_text(f"{title}\n\nВыберите товар:", reply_markup=kb)

# Детали товара
@dp.callback_query(lambda c: c.data.startswith('product_'))
async def show_product(cb: CallbackQuery):
    await cb.answer()
    pid = cb.data.split('_')[1]
    p = PRODUCTS[pid]
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Купить", callback_data=f"buy_{pid}")],
        [InlineKeyboardButton(text="🔙 К товарам", callback_data='catalog')]
    ])
    await cb.message.edit_text(f"{p['image']} {p['name']}\n\n💰 Цена: {p['price']:,} ₸\n📝 Описание: {p['description']}", reply_markup=kb)

# Покупка
@dp.callback_query(lambda c: c.data.startswith('buy_'))
async def buy_product(cb: CallbackQuery):
    await cb.answer()
    pid = cb.data.split('_')[1]
    p = PRODUCTS[pid]
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 В каталог", callback_data='catalog')]])
    await cb.message.edit_text(f"✅ Вы купили {p['name']} за {p['price']:,} ₸!\nМенеджер свяжется с вами.", reply_markup=kb)

# О магазине
@dp.callback_query(lambda c: c.data=='about')
async def about(cb: CallbackQuery):
    await cb.answer()
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Главное меню", callback_data='back_to_main')]])
    await cb.message.edit_text(
        "ℹ️ О магазине Наурызбай\n\n🏪 С 2020 года\n⭐ 5000+ клиентов\n🚚 Доставка по Казахстану\n🤖 ИИ помощник отвечает 24/7", reply_markup=kb)

# Контакты
@dp.callback_query(lambda c: c.data=='contacts')
async def contacts(cb: CallbackQuery):
    await cb.answer()
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Главное меню", callback_data='back_to_main')]])
    await cb.message.edit_text(
        "📞 +7 (777) 123-45-67\n📧 info@nauryzbay.kz\n📍 Алматы, ул. Абая 150", reply_markup=kb)

# Главное меню назад
@dp.callback_query(lambda c: c.data=='back_to_main')
async def back_to_main(cb: CallbackQuery):
    await cb.answer()
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Каталог товаров", callback_data="catalog")],
        [InlineKeyboardButton(text="🤖 Чат с ИИ", callback_data="ai_chat")],
        [InlineKeyboardButton(text="ℹ️ О магазине", callback_data="about")],
        [InlineKeyboardButton(text="📞 Контакты", callback_data="contacts")]
    ])
    await cb.message.edit_text("🛒 Добро пожаловать в магазин Наурызбай!", reply_markup=kb)

# Обработчик AI чата и прочие сообщения
@dp.callback_query(lambda c: c.data=='ai_chat')
async def ai_intro(cb: CallbackQuery):
    await cb.answer()
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🔙 Главное меню", callback_data='back_to_main')]])
    await cb.message.edit_text("🤖 Напишите любое сообщение — ИИ ответит!", reply_markup=kb)

@dp.message_handler()
async def ai_chat(message: Message):
    global message_count
    message_count += 1
    await bot.send_chat_action(message.chat.id, "typing")
    history = [
        {"role":"system","content":"Ты дружелюбный ИИ помощник магазина Наурызбай."},
        {"role":"user","content":message.text}
    ]
    ai_text = await get_ai_response(history)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Каталог товаров", callback_data="catalog")],
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="back_to_main")]
    ])
    await message.reply(ai_text, reply_markup=kb)

# HTTP handlers
async def home_handler(request):
    uptime = time.time() - start_time
    return web.json_response({"status":"Бот работает","uptime":round(uptime,2),"msg":message_count})
async def ping_handler(request): return web.Response(text="pong")
async def health_handler(request): return web.json_response({"status":"healthy","bot_status":bot_status})
async def webhook_handler(request):
    js = await request.json(); upd=Update(**js); await dp.feed_update(bot, upd); return web.Response(text="OK")
async def setup_webhook(app):
    await bot.set_webhook(WEBHOOK_URL+WEBHOOK_PATH)
    logger.info("Webhook установлен")
app = web.Application()
app.router.add_get('/',home_handler)
app.router.add_get('/ping',ping_handler)
app.router.add_get('/health',health_handler)
app.router.add_post(WEBHOOK_PATH,webhook_handler)
app.on_startup.append(setup_webhook)

if __name__=='__main__':
    port=int(os.getenv('PORT',10000))
    web.run_app(app,host='0.0.0.0',port=port)
