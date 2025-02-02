from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from flask import Flask, request, jsonify
import asyncio

# Хранилище для ожидаемых сообщений от пользователей
user_states = {}
# Словарь для хранения маппинга пересланных сообщений
forwarded_messages = {}

# ID администратора (замените на настоящий ID админа)
GROUP_CHAT_ID = -4606605624

# URL для WebApp
web_app = WebAppInfo(url="https://translate.yandex.ru/?from=tableau_yabro")

# Инициализация Flask приложения
app = Flask(__name__)

# Токен вашего бота
TOKEN = "7571474973:AAF3bwSdOwf7MyZ6GM7-osHdYaJIGTZxzQg"

# Инициализация бота
application = Application.builder().token(TOKEN).build()

# Функция, вызываемая при нажатии на команду /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [KeyboardButton("Отзыв")],
        [KeyboardButton("Вопрос по доставке")],
        [KeyboardButton("Связаться с менеджером")],
        [KeyboardButton("Бронь стола", web_app=web_app)]
    ]
    reply_markup = ReplyKeyboardMarkup(
        keyboard=keyboard, resize_keyboard=True, one_time_keyboard=False
    )
    await update.message.reply_text(
        text="Здравствуйте! Выберите одну из опций ниже:",
        reply_markup=reply_markup
    )

# Обработчик нажатий на кнопку Отзыв
async def review_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    inline_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Яндекс Карты", url="https://yandex.ru/maps/org/chori/98310370984/reviews")],
        [InlineKeyboardButton("2ГИС", url="https://2gis.ru/voronezh/firm/70000001062575386/tab/reviews")]
    ])
    await update.message.reply_text(
        "Чтобы оставить отзыв перейдите по ссылке.",
        reply_markup=inline_keyboard
    )

# Обработчик нажатий на кнопку Вопрос по доставке        
async def handle_delivery_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    inline_keyboard = [
        [InlineKeyboardButton("Промокод за отзыв", callback_data="promo_code")],
        [InlineKeyboardButton("Оставить обращение", callback_data="leave_request")]
    ]
    reply_markup = InlineKeyboardMarkup(inline_keyboard)
    await update.message.reply_text(
        "Пожалуйста, выберите один из вариантов ниже:",
        reply_markup=reply_markup
    )

# Обработка сообщений пользователей в режиме ожидания
async def handle_contact_manager(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    user_states[user_id] = "awaiting_request"
    await update.message.reply_text(
        "Для связи с менеджером опишите вашу проблему, и мы передадим сообщение."
    )

# Обработчик callback-запросов
async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    if query.data == "promo_code":
        await query.edit_message_text(
            text="Пожалуйста, отправьте фото вашего отзыва, чтобы получить промокод."
        )
        user_states[user_id] = "awaiting_photo"
    elif query.data == "leave_request":
        await query.edit_message_text(
            text="Напишите ваше обращение для отправки менеджеру."
        )
        user_states[user_id] = "awaiting_request"

# Пересылка сообщений пользователей в группу
async def user_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    user_id = user.id
    original_message = update.message

    forwarded_message = await context.bot.forward_message(
        chat_id=GROUP_CHAT_ID,
        from_chat_id=original_message.chat.id,
        message_id=original_message.message_id,
    )

    forwarded_messages[forwarded_message.message_id] = {
        "user_id": user_id,
        "original_message_id": original_message.message_id,
    }
    await update.message.reply_text("Ваше сообщение отправлено менеджеру.")

# Обработка ответов менеджера из группы
async def group_reply_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        return

    replied_message_id = update.message.reply_to_message.message_id

    if replied_message_id not in forwarded_messages:
        return

    user_info = forwarded_messages[replied_message_id]
    user_id = user_info["user_id"]
    reply_text = update.message.text

    await context.bot.send_message(chat_id=user_id, text=f"Ответ менеджера: {reply_text}")
    await update.message.reply_text("Ответ доставлен пользователю.")

# Flask маршрут для Webhook
@app.route('/webhook', methods=['POST'])
def webhook():
    json_data = request.get_json()
    update = Update.de_json(json_data, application.bot)
    asyncio.run_coroutine_threadsafe(
        application.update_queue.put(update),
        application.job_queue._loop
    )
    return jsonify(success=True)

# Основная функция
def main():
    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("Отзыв"), review_handler))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("Вопрос по доставке"), handle_delivery_question))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("Связаться с менеджером"), handle_contact_manager))
    application.add_handler(CallbackQueryHandler(handle_callback_query))
    application.add_handler(MessageHandler(filters.ChatType.PRIVATE & ~filters.COMMAND, user_message_handler))
    application.add_handler(MessageHandler(filters.Chat(GROUP_CHAT_ID) & ~filters.COMMAND, group_reply_handler))

    # Установка Webhook
    webhook_url = "https://your_domain.com/webhook"
    application.run_webhook(
        listen="0.0.0.0",
        port=5000,
        url_path=f"/{TOKEN}",
        webhook_url=f"{webhook_url}/{TOKEN}"
    )

# Запуск Flask приложения
if __name__ == "__main__":
    main()
    app.run(port=5000)