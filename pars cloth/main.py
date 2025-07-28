import re
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ConversationHandler, ContextTypes
)

WAIT_QUERIES, WAIT_START_ID, WAIT_DONATE, WAIT_PRICE, WAIT_CATEGORY, WAIT_TORSO, CONFIRM_REPEAT = range(7)

def transform_query(query, new_id, donate, price_from_user, category, torso_new):
    pattern = re.compile(
        r"INSERT INTO clothes_male_tops\(id, cvariation, torso, textures, type, category, can_buy, price\)\s*VALUES\s*\('(\d+)',\s*'(\d+)',\s*'(\d+)',\s*'(\[.*?\])',\s*'(-?\d+)',\s*'(.*?)',\s*'(\d+)',\s*'(\d+)'\);"
    )
    match = pattern.match(query.strip())
    if not match:
        raise ValueError(f"Не удалось распарсить запрос: {query}")

    old_id, cvariation, torso_old, textures, _type, old_category, can_buy, price_old = match.groups()
    variation = old_id

    if donate == 0:
        if price_old != '0':
            donate_new = '0'
            price_new = price_old
        else:
            donate_new = '0'
            price_new = str(price_from_user)
    else:
        donate_new = str(donate)
        price_new = '0'

    return (
        "INSERT INTO clothes_male_tops("
        "id, variation, cvariation, torso, textures, donate, price, category, "
        "similar, type, undershirt, undershirt_buttoned, undershirt_buttoned_torso, isClearLegs"
        ") VALUES ("
        f"'{new_id}', '{variation}', '-1', '{torso_new}', '{textures}', "
        f"'{donate_new}', '{price_new}', '{category}', "
        "'-1', '0', '-1', '-1', '-1', '0'"
        ");"
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Вставь все SQL-запросы одним сообщением, каждый с новой строки."
    )
    return WAIT_QUERIES

async def receive_queries(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    queries = [line.strip() for line in text.split('\n') if line.strip()]
    if not queries:
        await update.message.reply_text("Пожалуйста, отправь хотя бы один запрос.")
        return WAIT_QUERIES
    context.user_data['queries'] = queries
    await update.message.reply_text("Введи стартовый ID для новых запросов:")
    return WAIT_START_ID

async def receive_start_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        start_id = int(update.message.text.strip())
        context.user_data['start_id'] = start_id
        await update.message.reply_text("Введи значение donate (0 — если нужно указать цену вручную):")
        return WAIT_DONATE
    except:
        await update.message.reply_text("Введите корректный числовой ID.")
        return WAIT_START_ID

async def receive_donate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        donate = int(update.message.text.strip())
        context.user_data['donate'] = donate
        if donate == 0:
            await update.message.reply_text("Введи значение price (если в запросе оно 0):")
            return WAIT_PRICE
        else:
            context.user_data['price'] = 0
            await update.message.reply_text("Введи значение category:")
            return WAIT_CATEGORY
    except:
        await update.message.reply_text("Введите целое число.")
        return WAIT_DONATE

async def receive_price(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        price = int(update.message.text.strip())
        context.user_data['price'] = price
        await update.message.reply_text("Введи значение category:")
        return WAIT_CATEGORY
    except:
        await update.message.reply_text("Введите целое число.")
        return WAIT_PRICE

async def receive_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    category = update.message.text.strip()
    context.user_data['category'] = category
    await update.message.reply_text("Введи значение torso (например, 0):")
    return WAIT_TORSO

async def receive_torso(update: Update, context: ContextTypes.DEFAULT_TYPE):
    torso = update.message.text.strip()
    # Можно проверить, что torso — число, но необязательно
    context.user_data['torso'] = torso

    queries = context.user_data['queries']
    start_id = context.user_data['start_id']
    donate = context.user_data['donate']
    price = context.user_data['price']
    category = context.user_data['category']
    torso_new = context.user_data['torso']

    results = []
    for i, q in enumerate(queries):
        try:
            new_q = transform_query(q, start_id + i, donate, price, category, torso_new)
            results.append(new_q)
        except ValueError as e:
            results.append(f"❌ Ошибка в запросе #{i+1}: {e}")

    chunk_size = 20
    for i in range(0, len(results), chunk_size):
        chunk = results[i:i + chunk_size]
        await update.message.reply_text("\n\n".join(chunk))

    keyboard = [["Да", "Нет"]]
    await update.message.reply_text(
        "Хотите обработать ещё запросы?",
        reply_markup=ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    return CONFIRM_REPEAT

async def confirm_repeat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text.strip().lower() == "да":
        await update.message.reply_text("Вставь все SQL-запросы одним сообщением, каждый с новой строки:", reply_markup=None)
        return WAIT_QUERIES
    else:
        await update.message.reply_text("Спасибо! Чтобы начать снова, напиши /start", reply_markup=None)
        return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Операция отменена.")
    return ConversationHandler.END

def main():
    TOKEN = "8169585431:AAEo-xbnOiCRaz9dlTexinVMpXb3zmbIFvw"

    app = ApplicationBuilder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            WAIT_QUERIES: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_queries)],
            WAIT_START_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_start_id)],
            WAIT_DONATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_donate)],
            WAIT_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_price)],
            WAIT_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_category)],
            WAIT_TORSO: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_torso)],
            CONFIRM_REPEAT: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_repeat)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.run_polling()

if __name__ == "__main__":
    main()
