import asyncio
import logging
import os
import time
from datetime import datetime
from aiohttp import web, ClientSession
import aiogram
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, Update
from openai import OpenAI
import json

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Получение токенов из переменных окружения
BOT_TOKEN = os.getenv('BOT_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

if not BOT_TOKEN:
    logger.error("BOT_TOKEN не найден в переменных окружения!")
    exit(1)

if not OPENAI_API_KEY:
    logger.error("OPENAI_API_KEY не найден в переменных окружения!")
    exit(1)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Настройка OpenAI (новый способ)
openai_client = OpenAI(api_key=OPENAI_API_KEY)

# Статистика
start_time = time.time()
message_count = 0
bot_status = "initialized"

# URL для webhook
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"https://telegram-bot-24-7.onrender.com{WEBHOOK_PATH}"

# База данных товаров
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

# Обработчики команд
@dp.message(Command("start"))
async def cmd_start(message: Message):
    global message_count
    message_count += 1
    
    logger.info(f"Пользователь {message.from_user.id} запустил бота")
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Каталог товаров", callback_data="catalog")],
        [InlineKeyboardButton(text="🤖 Чат с ИИ", callback_data="ai_chat")],
        [InlineKeyboardButton(text="ℹ️ О магазине", callback_data="about")],
        [InlineKeyboardButton(text="📞 Контакты", callback_data="contacts")]
    ])
    
    await message.answer(
        f"🛒 Добро пожаловать в магазин Наурызбай!\n\n"
        f"👋 Привет, {message.from_user.first_name}!\n"
        f"Здесь вы можете:\n"
        f"🛒 Найти качественные товары по доступным ценам\n"
        f"🤖 Пообщаться с ИИ помощником\n\n"
        f"📱 Выберите нужный раздел:",
        reply_markup=keyboard
    )

@dp.message(Command("ai"))
async def cmd_ai(message: Message):
    """Команда для быстрого доступа к ИИ"""
    await message.answer(
        "🤖 Привет! Я ИИ помощник магазина Наурызбай.\n\n"
        "💬 Просто напишите мне любое сообщение, и я отвечу!\n"
        "Я могу помочь с:\n"
        "• Вопросами о товарах\n"
        "• Общением на любые темы\n"
        "• Советами по покупкам\n"
        "• Информацией о магазине\n\n"
        "✨ Задайте свой вопрос!"
    )

@dp.callback_query(lambda c: c.data == "ai_chat")
async def process_ai_chat(callback_query: CallbackQuery):
    await callback_query.answer()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="back_to_main")]
    ])
    
    await callback_query.message.edit_text(
        "🤖 ИИ Помощник магазина Наурызбай\n\n"
        "💬 Просто напишите мне любое сообщение, и я отвечу!\n\n"
        "Я могу помочь с:\n"
        "• Вопросами о товарах и ценах\n"
        "• Рекомендациями по выбору\n"
        "• Общением на любые темы\n"
        "• Информацией о магазине\n\n"
        "✨ Задайте свой вопрос!",
        reply_markup=keyboard
    )

@dp.callback_query(lambda c: c.data == "catalog")
async def process_catalog(callback_query: CallbackQuery):
    await callback_query.answer()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📱 Электроника", callback_data="category_electronics")],
        [InlineKeyboardButton(text="🏠 Для дома", callback_data="category_home")],
        [InlineKeyboardButton(text="🎮 Развлечения", callback_data="category_entertainment")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
    ])
    
    await callback_query.message.edit_text(
        "🛒 Каталог товаров\n\n"
        "Выберите категорию:",
        reply_markup=keyboard
    )

@dp.callback_query(lambda c: c.data.startswith("category_"))
async def process_category(callback_query: CallbackQuery):
    await callback_query.answer()
    category = callback_query.data.split("_")[1]
    
    if category == "electronics":
        products = ["1", "2", "3", "4", "5"]
        title = "📱 Электроника"
    elif category == "home":
        products = ["7", "8", "10"]
        title = "🏠 Для дома"
    elif category == "entertainment":
        products = ["6", "9", "11"]
        title = "🎮 Развлечения"
    
    keyboard_rows = []
    for product_id in products:
        product = PRODUCTS[product_id]
        keyboard_rows.append([InlineKeyboardButton(
            text=f"{product['image']} {product['name']} - {product['price']:,} ₸",
            callback_data=f"product_{product_id}"
        )])
    
    keyboard_rows.append([InlineKeyboardButton(text="🔙 К каталогу", callback_data="catalog")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_rows)
    
    await callback_query.message.edit_text(
        f"{title}\n\n"
        "Выберите товар:",
        reply_markup=keyboard
    )

@dp.callback_query(lambda c: c.data.startswith("product_"))
async def process_product(callback_query: CallbackQuery):
    await callback_query.answer()
    product_id = callback_query.data.split("_")[1]
    product = PRODUCTS[product_id]
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Купить", callback_data=f"buy_{product_id}")],
        [InlineKeyboardButton(text="🔙 К категории", callback_data="catalog")]
    ])
    
    await callback_query.message.edit_text(
        f"{product['image']} {product['name']}\n\n"
        f"💰 Цена: {product['price']:,} ₸\n"
        f"📝 Описание: {product['description']}\n\n"
        f"🛒 Хотите купить этот товар?",
        reply_markup=keyboard
    )

@dp.callback_query(lambda c: c.data.startswith("buy_"))
async def process_buy(callback_query: CallbackQuery):
    await callback_query.answer()
    product_id = callback_query.data.split("_")[1]
    product = PRODUCTS[product_id]
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 К товарам", callback_data="catalog")]
    ])
    
    await callback_query.message.edit_text(
        f"✅ Спасибо за покупку!\n\n"
        f"🛒 Товар: {product['name']}\n"
        f"💰 Сумма: {product['price']:,} ₸\n\n"
        f"📞 Наш менеджер свяжется с вами в ближайшее время для подтверждения заказа.\n\n"
        f"🎉 Удачных покупок!",
        reply_markup=keyboard
    )

@dp.callback_query(lambda c: c.data == "about")
async def process_about(callback_query: CallbackQuery):
    await callback_query.answer()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="back_to_main")]
    ])
    
    await callback_query.message.edit_text(
        "ℹ️ О магазине Наурызбай\n\n"
        "🏪 Мы работаем с 2020 года\n"
        "⭐ 5000+ довольных клиентов\n"
        "🚚 Доставка по всему Казахстану\n"
        "💯 Гарантия качества\n"
        "🕐 Работаем 24/7\n"
        "🤖 ИИ помощник для консультаций\n\n"
        "🎯 Наша цель - предоставить вам лучшие товары по доступным ценам!",
        reply_markup=keyboard
    )

@dp.callback_query(lambda c: c.data == "contacts")
async def process_contacts(callback_query: CallbackQuery):
    await callback_query.answer()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Главное меню", callback_data="back_to_main")]
    ])
    
    await callback_query.message.edit_text(
        "📞 Контакты\n\n"
        "📱 Телефон: +7 (777) 123-45-67\n"
        "📧 Email: info@nauryzbay.kz\n"
        "📍 Адрес: г. Алматы, ул. Абая 150\n"
        "🕐 Режим работы: 24/7\n\n"
        "💬 Telegram: @nauryzbay_support\n"
        "📲 WhatsApp: +7 (777) 123-45-67\n\n"
        "🤖 Или просто напишите любое сообщение - ИИ помощник ответит!",
        reply_markup=keyboard
    )

@dp.callback_query(lambda c: c.data == "back_to_main")
async def back_to_main(callback_query: CallbackQuery):
    await callback_query.answer()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🛒 Каталог товаров", callback_data="catalog")],
        [InlineKeyboardButton(text="🤖 Чат с ИИ", callback_data="ai_chat")],
        [InlineKeyboardButton(text="ℹ️ О магазине", callback_data="about")],
        [InlineKeyboardButton(text="📞 Контакты", callback_data="contacts")]
    ])
    
    await callback_query.message.edit_text(
        f"🛒 Магазин Наурызбай\n\n"
        f"👋 Добро пожаловать обратно!\n"
        f"🤖 Теперь с ИИ помощником!\n\n"
        f"📱 Выберите нужный раздел:",
        reply_markup=keyboard
    )

# Обработчик всех остальных сообщений - ИИ помощник
@dp.message()
async def handle_message(message: Message):
    global message_count
    message_count += 1
    
    # Показываем что бот печатает
    await bot.send_chat_action(chat_id=message.chat.id, action="typing")
    
    # ИИ ответ с новым API
    try:
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": """Ты дружелюбный ИИ помощник магазина Наурызбай в Казахстане. 
                
Твои задачи:
- Отвечать на любые вопросы пользователей дружелюбно и полезно
- Помогать с выбором товаров в магазине 
- Консультировать по товарам: iPhone 15 (350,000₸), MacBook Air (450,000₸), AirPods Pro (120,000₸), Apple Watch (180,000₸), iPad Air (280,000₸), PlayStation 5 (320,000₸), кофемашина Nespresso (85,000₸), пылесос Dyson V15 (220,000₸), электросамокат Xiaomi (150,000₸), фитнес-браслет Xiaomi Band (25,000₸), колонка JBL (45,000₸)
- Общаться на любые темы, не только о магазине
- Говорить на русском языке
- Быть полезным и интересным собеседником

Отвечай естественно, как живой человек. Используй эмодзи для выразительности."""},
                {"role": "user", "content": message.text}
            ],
            max_tokens=300,
            temperature=0.7
        )
        
        ai_response = response.choices[0].message.content
        
        # Добавляем кнопку для перехода к каталогу
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🛒 Каталог товаров", callback_data="catalog")],
            [InlineKeyboardButton(text="📱 Главное меню", callback_data="back_to_main")]
        ])
        
        await message.reply(
            f"🤖 {ai_response}",
            reply_markup=keyboard
        )
        
        logger.info(f"ИИ ответил пользователю {message.from_user.id}")
        
    except Exception as e:
        logger.error(f"Ошибка OpenAI: {e}")
        
        # Запасной ответ если ИИ не работает
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🛒 Каталог товаров", callback_data="catalog")],
            [InlineKeyboardButton(text="📱 Главное меню", callback_data="back_to_main")]
        ])
        
        await message.reply(
            "🤖 Привет! Я ИИ помощник магазина Наурызбай.\n\n"
            "Сейчас у меня небольшие технические трудности, но я все равно готов помочь!\n\n"
            "🛒 У нас есть отличные товары:\n"
            "📱 iPhone 15 - 350,000₸\n"
            "💻 MacBook Air - 450,000₸\n"
            "🎧 AirPods Pro - 120,000₸\n"
            "⌚ Apple Watch - 180,000₸\n"
            "И многое другое!\n\n"
            "💬 Напишите еще раз - я постараюсь ответить лучше!",
            reply_markup=keyboard
        )

# Веб-обработчики
async def home_handler(request):
    uptime = time.time() - start_time
    return web.json_response({
        "status": "Наурызбай магазин бот с ИИ работает! 🛒🤖",
        "bot_status": bot_status,
        "webhook_url": WEBHOOK_URL,
        "uptime_seconds": round(uptime, 2),
        "uptime_hours": round(uptime / 3600, 2),
        "messages_processed": message_count,
        "товаров_в_наличии": len(PRODUCTS),
        "ai_status": "active" if OPENAI_API_KEY else "disabled"
    })

async def ping_handler(request):
    return web.Response(text="pong")

async def health_handler(request):
    return web.json_response({
        "status": "healthy", 
        "bot_status": bot_status,
        "ai_status": "active" if OPENAI_API_KEY else "disabled",
        "timestamp": datetime.now().isoformat()
    })

# Webhook обработчик
async def webhook_handler(request):
    try:
        update_dict = await request.json()
        update = Update(**update_dict)
        
        # Обрабатываем update
        await dp.feed_update(bot, update)
        
        return web.Response(text="OK")
    except Exception as e:
        logger.error(f"Ошибка webhook: {e}")
        return web.Response(text="ERROR", status=500)

# Функция для настройки webhook
async def setup_webhook():
    global bot_status
    try:
        logger.info(f"🔗 Настройка webhook: {WEBHOOK_URL}")
        await bot.set_webhook(url=WEBHOOK_URL)
        bot_status = "webhook_active"
        logger.info("✅ Webhook успешно настроен!")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка настройки webhook: {e}")
        bot_status = f"webhook_error: {e}"
        return False

# Создание приложения
async def create_app():
    app = web.Application()
    
    # Маршруты
    app.router.add_get('/', home_handler)
    app.router.add_get('/ping', ping_handler)
    app.router.add_get('/health', health_handler)
    app.router.add_post(WEBHOOK_PATH, webhook_handler)
    
    return app

# Главная функция
async def main():
    logger.info("🚀 Запуск магазина Наурызбай с ИИ помощником...")
    
    # Настройка webhook
    logger.info("🔗 Настройка Telegram webhook...")
    if await setup_webhook():
        logger.info("✅ Webhook настроен успешно")
    else:
        logger.error("❌ Не удалось настроить webhook")
    
    # Создание и запуск веб-приложения
    app = await create_app()
    
    port = int(os.environ.get('PORT', 10000))
    logger.info(f"🌐 Запуск aiohttp сервера на порту {port}...")
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    logger.info("🎉 Сервер с ИИ помощником запущен и готов к работе!")
    
    # Держим сервер запущенным
    try:
        while True:
            await asyncio.sleep(3600)  # Проверяем каждый час
    except KeyboardInterrupt:
        logger.info("🛑 Остановка сервера...")
    finally:
        await runner.cleanup()

if __name__ == "__main__":
    asyncio.run(main())
