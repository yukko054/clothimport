import re
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ConversationHandler, ContextTypes
)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Состояния диалога
(
    WAIT_QUERIES, WAIT_TABLE_TYPE, WAIT_START_ID, 
    WAIT_DONATE, WAIT_PRICE, WAIT_CATEGORY,
    WAIT_TORSO, WAIT_ISHAIR, WAIT_ISHAT, WAIT_ISGLASSES,
    WAIT_CLEARHAIR, WAIT_MAXSLOTS, WAIT_UNDERWEAR,
    CONFIRM_REPEAT
) = range(14)

# Конфигурация (вынесите в отдельный файл config.py)
ALLOWED_USERS = [7987332507]  # Замените на ваш Telegram ID
BOT_TOKEN = "8169585431:AAEo-xbnOiCRaz9dlTexinVMpXb3zmbIFvw"  # Замените на ваш токен

def check_access(user_id: int) -> bool:
    """Проверяет, есть ли у пользователя доступ к боту"""
    return user_id in ALLOWED_USERS

async def check_user_access(update: Update) -> bool:
    """Проверяет доступ пользователя"""
    user_id = update.effective_user.id
    if not check_access(user_id):
        await update.message.reply_text("⛔ Доступ запрещен!")
        return False
    return True

def transform_query(query: str, table_type: str, new_id: int, donate: int, 
                   price: int, category: str, **kwargs) -> str:
    """Преобразует SQL-запрос в нужный формат"""
    patterns = {
        "clothes_male_tops": r"INSERT INTO clothes_male_tops\(id, cvariation, textures, category, can_buy, price\)\s*VALUES\s*\('(\d+)',\s*'(-?\d+)',\s*'(\[.*?\])',\s*'(.*?)',\s*'(\d+)',\s*'(\d+)'\);",
        "clothes_male_glasses": r"INSERT INTO clothes_male_glasses\(id, cvariation, textures, category, can_buy, price\)\s*VALUES\s*\('(\d+)',\s*'(-?\d+)',\s*'(\[.*?\])',\s*'(.*?)',\s*'(\d+)',\s*'(\d+)'\);",
        "clothes_male_accessories": r"INSERT INTO clothes_male_accessories\(id, cvariation, textures, category, can_buy, price\)\s*VALUES\s*\('(\d+)',\s*'(-?\d+)',\s*'(\[.*?\])',\s*'(.*?)',\s*'(\d+)',\s*'(\d+)'\);",
        "clothes_male_masks": r"INSERT INTO clothes_male_masks\(id, cvariation, textures, category, can_buy, price\)\s*VALUES\s*\('(\d+)',\s*'(-?\d+)',\s*'(\[.*?\])',\s*'(.*?)',\s*'(\d+)',\s*'(\d+)'\);",
        "clothes_male_hats": r"INSERT INTO clothes_male_hats\(id, cvariation, textures, category, can_buy, price\)\s*VALUES\s*\('(\d+)',\s*'(-?\d+)',\s*'(\[.*?\])',\s*'(.*?)',\s*'(\d+)',\s*'(\d+)'\);",
        "clothes_male_legs": r"INSERT INTO clothes_male_legs\(id, cvariation, textures, category, can_buy, price\)\s*VALUES\s*\('(\d+)',\s*'(-?\d+)',\s*'(\[.*?\])',\s*'(.*?)',\s*'(\d+)',\s*'(\d+)'\);",
        "clothes_male_shoes": r"INSERT INTO clothes_male_shoes\(id, cvariation, textures, category, can_buy, price\)\s*VALUES\s*\('(\d+)',\s*'(-?\d+)',\s*'(\[.*?\])',\s*'(.*?)',\s*'(\d+)',\s*'(\d+)'\);",
        "clothes_male_watches": r"INSERT INTO clothes_male_watches\(id, cvariation, textures, category, can_buy, price\)\s*VALUES\s*\('(\d+)',\s*'(-?\d+)',\s*'(\[.*?\])',\s*'(.*?)',\s*'(\d+)',\s*'(\d+)'\);",
        "clothes_male_bags": r"INSERT INTO clothes_male_bags\(id, cvariation, textures, category, can_buy, price\)\s*VALUES\s*\('(\d+)',\s*'(-?\d+)',\s*'(\[.*?\])',\s*'(.*?)',\s*'(\d+)',\s*'(\d+)'\);",
        "clothes_male_bodyarmors": r"INSERT INTO clothes_male_bodyarmors\(id, cvariation, textures, category, can_buy, price\)\s*VALUES\s*\('(\d+)',\s*'(-?\d+)',\s*'(\[.*?\])',\s*'(.*?)',\s*'(\d+)',\s*'(\d+)'\);"
    }

    pattern = re.compile(patterns.get(table_type))
    match = pattern.match(query.strip())
    if not match:
        raise ValueError(f"Не удалось распарсить запрос: {query}")

    old_id, cvariation, textures, old_category, can_buy, price_old = match.groups()
    
    if donate == 0:
        if price_old != '0':
            donate_new = '0'
            price_new = price_old
        else:
            donate_new = '0'
            price_new = str(price)
    else:
        donate_new = str(donate)
        price_new = '0'

    base_fields = {
        "id": new_id,
        "variation": old_id,
        "cvariation": "-1",
        "textures": textures,
        "donate": donate_new,
        "price": price_new,
        "category": category
    }

    table_specific = {
        "clothes_male_tops": {
            "torso": kwargs.get('torso', '0'),
            "similar": "-1",
            "type": "0",
            "undershirt": "-1",
            "undershirt_buttoned": "-1",
            "undershirt_buttoned_torso": "-1",
            "isClearLegs": "0"
        },
        "clothes_male_masks": {
            "gender": "-1",
            "isHair": kwargs.get('ishair', '0'),
            "isHat": kwargs.get('ishat', '0'),
            "isGlasses": kwargs.get('isglasses', '0')
        },
        "clothes_male_hats": {
            "clearHair": kwargs.get('clearhair', '0'),
            "similar": "-1"
        },
        "clothes_male_legs": {
            "underwear": kwargs.get('underwear', '0'),
            "similar": "-1"
        },
        "clothes_male_bags": {
            "maxSlots": kwargs.get('maxslots', '0')
        },
        "clothes_male_bodyarmors": {
            "similar": "-1"
        }
    }

    fields = {**base_fields, **table_specific.get(table_type, {})}
    
    columns = ", ".join(fields.keys())
    values = ", ".join([f"'{v}'" for v in fields.values()])
    
    return f"INSERT INTO {table_type}({columns}) VALUES ({values});"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Начало диалога"""
    if not await check_user_access(update):
        return ConversationHandler.END
        
    await update.message.reply_text(
        "Привет! Я бот для преобразования SQL-запросов.\n"
        "Отправь мне SQL-запросы для преобразования (каждый с новой строки)."
    )
    return WAIT_QUERIES

async def receive_queries(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получаем SQL-запросы от пользователя"""
    if not await check_user_access(update):
        return ConversationHandler.END
        
    queries = [q.strip() for q in update.message.text.split('\n') if q.strip()]
    if not queries:
        await update.message.reply_text("Не обнаружено SQL-запросов. Попробуйте снова.")
        return WAIT_QUERIES
    
    first_query = queries[0].lower()
    table_types = {
        "clothes_male_tops": {"param": "torso", "state": WAIT_TORSO},
        "clothes_male_masks": {"params": [
            {"name": "isHair", "question": "Это маска с волосами? (1 - да, 0 - нет):", "state": WAIT_ISHAIR},
            {"name": "isHat", "question": "Это маска с шляпой? (1 - да, 0 - нет):", "state": WAIT_ISHAT},
            {"name": "isGlasses", "question": "Это маска с очками? (1 - да, 0 - нет):", "state": WAIT_ISGLASSES}
        ]},
        "clothes_male_hats": {"param": "clearHair", "question": "Очищать волосы? (1 - да, 0 - нет):", "state": WAIT_CLEARHAIR},
        "clothes_male_legs": {"param": "underwear", "question": "Это нижнее белье? (1 - да, 0 - нет):", "state": WAIT_UNDERWEAR},
        "clothes_male_bags": {"param": "maxSlots", "question": "Введите maxSlots (число слотов):", "state": WAIT_MAXSLOTS}
    }

    table_type = None
    extra_params = None
    
    for t in table_types:
        if t in first_query:
            table_type = t
            extra_params = table_types[t]
            break
    
    if not table_type:
        for t in ["clothes_male_glasses", "clothes_male_accessories", 
                 "clothes_male_shoes", "clothes_male_watches", "clothes_male_bodyarmors"]:
            if t in first_query:
                table_type = t
                break
    
    if not table_type:
        await update.message.reply_text("Неизвестный тип таблицы.")
        return WAIT_QUERIES
    
    context.user_data.update({
        'queries': queries,
        'table_type': table_type,
        'extra_params': extra_params
    })
    
    await update.message.reply_text(f"Определена таблица: {table_type}. Введите начальный ID:")
    return WAIT_START_ID

async def receive_start_id(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получаем начальный ID"""
    if not await check_user_access(update):
        return ConversationHandler.END
        
    try:
        start_id = int(update.message.text)
        context.user_data['start_id'] = start_id
        await update.message.reply_text("Введите сумму доната (0 если используется цена):")
        return WAIT_DONATE
    except ValueError:
        await update.message.reply_text("ID должен быть числом. Попробуйте снова.")
        return WAIT_START_ID

async def receive_donate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получаем сумму доната"""
    if not await check_user_access(update):
        return ConversationHandler.END
        
    try:
        donate = int(update.message.text)
        context.user_data['donate'] = donate
        
        if donate == 0:
            await update.message.reply_text("Введите цену:")
            return WAIT_PRICE
        else:
            context.user_data['price'] = 0
            await update.message.reply_text("Введите категорию:")
            return WAIT_CATEGORY
    except ValueError:
        await update.message.reply_text("Сумма должна быть числом. Попробуйте снова.")
        return WAIT_DONATE

async def receive_price(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получаем цену"""
    if not await check_user_access(update):
        return ConversationHandler.END
        
    try:
        price = int(update.message.text)
        context.user_data['price'] = price
        await update.message.reply_text("Введите категорию:")
        return WAIT_CATEGORY
    except ValueError:
        await update.message.reply_text("Цена должна быть числом. Попробуйте снова.")
        return WAIT_PRICE

async def receive_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Получаем категорию"""
    if not await check_user_access(update):
        return ConversationHandler.END
        
    category = update.message.text.strip()
    context.user_data['category'] = category
    
    extra_params = context.user_data.get('extra_params')
    
    if not extra_params:
        return await process_queries(update, context)
    
    if 'param' in extra_params:
        await update.message.reply_text(extra_params["question"])
        return extra_params["state"]
    elif 'params' in extra_params:
        context.user_data['current_param'] = 0
        param = extra_params["params"][0]
        await update.message.reply_text(param["question"])
        return param["state"]

async def receive_torso(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик для параметра torso"""
    if not await check_user_access(update):
        return ConversationHandler.END
        
    try:
        torso = int(update.message.text)
        if torso not in [0, 1]:
            await update.message.reply_text("Введите 0 или 1:")
            return WAIT_TORSO
        context.user_data['torso'] = str(torso)
        return await process_queries(update, context)
    except ValueError:
        await update.message.reply_text("Введите число 0 или 1:")
        return WAIT_TORSO

async def receive_ishair(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик для параметра isHair"""
    if not await check_user_access(update):
        return ConversationHandler.END
        
    if update.message.text not in ['0', '1']:
        await update.message.reply_text("Введите 1 (да) или 0 (нет):")
        return WAIT_ISHAIR
    context.user_data['ishair'] = update.message.text
    return await receive_ishat(update, context)

async def receive_ishat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик для параметра isHat"""
    if not await check_user_access(update):
        return ConversationHandler.END
        
    if update.message.text not in ['0', '1']:
        await update.message.reply_text("Введите 1 (да) или 0 (нет):")
        return WAIT_ISHAT
    context.user_data['ishat'] = update.message.text
    return await receive_isglasses(update, context)

async def receive_isglasses(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик для параметра isGlasses"""
    if not await check_user_access(update):
        return ConversationHandler.END
        
    if update.message.text not in ['0', '1']:
        await update.message.reply_text("Введите 1 (да) или 0 (нет):")
        return WAIT_ISGLASSES
    context.user_data['isglasses'] = update.message.text
    return await process_queries(update, context)

async def receive_clearhair(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик для параметра clearHair"""
    if not await check_user_access(update):
        return ConversationHandler.END
        
    if update.message.text not in ['0', '1']:
        await update.message.reply_text("Введите 1 (да) или 0 (нет):")
        return WAIT_CLEARHAIR
    context.user_data['clearhair'] = update.message.text
    return await process_queries(update, context)

async def receive_underwear(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик для параметра underwear"""
    if not await check_user_access(update):
        return ConversationHandler.END
        
    if update.message.text not in ['0', '1']:
        await update.message.reply_text("Введите 1 (да) или 0 (нет):")
        return WAIT_UNDERWEAR
    context.user_data['underwear'] = update.message.text
    return await process_queries(update, context)

async def receive_maxslots(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработчик для параметра maxSlots"""
    if not await check_user_access(update):
        return ConversationHandler.END
        
    try:
        maxslots = int(update.message.text)
        if maxslots < 0:
            await update.message.reply_text("Введите положительное число:")
            return WAIT_MAXSLOTS
        context.user_data['maxslots'] = str(maxslots)
        return await process_queries(update, context)
    except ValueError:
        await update.message.reply_text("Введите целое число:")
        return WAIT_MAXSLOTS

async def process_queries(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка всех запросов"""
    if not await check_user_access(update):
        return ConversationHandler.END
        
    queries = context.user_data['queries']
    table_type = context.user_data['table_type']
    start_id = context.user_data['start_id']
    donate = context.user_data['donate']
    price = context.user_data.get('price', 0)
    category = context.user_data['category']
    
    extra_params = {}
    param_names = ['torso', 'ishair', 'ishat', 'isglasses', 'clearhair', 'underwear', 'maxslots']
    for p in param_names:
        if p in context.user_data:
            extra_params[p] = context.user_data[p]
    
    results = []
    for i, query in enumerate(queries):
        try:
            new_query = transform_query(
                query, table_type, start_id + i, donate, price, category, **extra_params
            )
            results.append(new_query)
        except ValueError as e:
            results.append(f"Ошибка в запросе {i+1}: {str(e)}")
    
    for i in range(0, len(results), 5):
        chunk = results[i:i+5]
        await update.message.reply_text("\n\n".join(chunk))
    
    keyboard = [["Да", "Нет"]]
    await update.message.reply_text(
        "Хотите преобразовать еще запросы?",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return CONFIRM_REPEAT

async def confirm_repeat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Подтверждение повторения"""
    if not await check_user_access(update):
        return ConversationHandler.END
        
    if update.message.text.lower() == 'да':
        await update.message.reply_text("Отправьте SQL-запросы для преобразования:")
        return WAIT_QUERIES
    else:
        await update.message.reply_text("Работа завершена. Для начала снова используйте /start")
        return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отмена операции"""
    if not await check_user_access(update):
        return ConversationHandler.END
        
    await update.message.reply_text("Операция отменена.")
    return ConversationHandler.END

def main() -> None:
    """Запуск бота"""
    application = ApplicationBuilder().token(BOT_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            WAIT_QUERIES: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_queries)],
            WAIT_START_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_start_id)],
            WAIT_DONATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_donate)],
            WAIT_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_price)],
            WAIT_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_category)],
            WAIT_TORSO: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_torso)],
            WAIT_ISHAIR: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_ishair)],
            WAIT_ISHAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_ishat)],
            WAIT_ISGLASSES: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_isglasses)],
            WAIT_CLEARHAIR: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_clearhair)],
            WAIT_UNDERWEAR: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_underwear)],
            WAIT_MAXSLOTS: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_maxslots)],
            CONFIRM_REPEAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_repeat)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == '__main__':
    main()