from telegram import Update, KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from telegram.error import ChatMigrated

# Хранилище для ожидаемых сообщений от пользователей
user_states = {}
# Словарь для хранения маппинга пересланных сообщений
forwarded_messages = {}

# ID администратора (замените на настоящий ID админа)
GROUP_CHAT_ID = -1002277561873

# URL для WebApp
web_app = WebAppInfo(url="https://choribot.ru/")

# Токен вашего бота
TOKEN = "7571474973:AAF3bwSdOwf7MyZ6GM7-osHdYaJIGTZxzQg"

# Инициализация бота
application = Application.builder().token(TOKEN).build()

# Функция, вызываемая при нажатии на команду /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    inline_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Бронь стола", web_app=web_app)],  # Inline кнопка с WebApp
        [InlineKeyboardButton("Отзыв", callback_data="review")],  # Кнопка с callback_data
        [InlineKeyboardButton("Вопрос по доставке", callback_data="delivery_question")],  # Кнопка с callback_data
        [InlineKeyboardButton("Связаться с менеджером", callback_data="contact_manager")]  # Ещё одна Inline кнопка
    ])
    await update.message.reply_text(
        text="Намасте, друзья☀️\n\nРады приветствовать вас в нашем чат-боте! Здесь вы сможете получить ответы на ваши вопросы, оставить отзыв на удобной площадке, а также забронировать столик в один клик. \n\nВыберите, пожалуйста, нужную вам опцию🧘🏼‍♀️",
        reply_markup=inline_keyboard
    )

# Обработчик callback-запросов
async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "review":
        inline_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Яндекс Карты", url="https://yandex.ru/maps/org/chori/98310370984/reviews")],
            [InlineKeyboardButton("2ГИС", url="https://2gis.ru/voronezh/firm/70000001062575386/tab/reviews")]
        ])
        await query.message.reply_text(
            "Нам безумно приятно, когда вы оставляете свое мнение о нашей работе!"
            " Пожалуйста, поделитесь отзывом о нашем заведении, используя платформу ниже ⬇️",
            reply_markup=inline_keyboard
        )

    elif query.data == "delivery_question":
        inline_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("Промокод за отзыв", callback_data="promo_code")],
            [InlineKeyboardButton("Оставить обращение", callback_data="leave_request")]
        ])
        await query.message.reply_text(
            "Если у вас возникли вопросы по доставке, выберите одну из предложенных опций ⬇️",
            reply_markup=inline_keyboard
        )
    elif query.data == "contact_manager":
        await query.message.reply_text(
            text="Пожалуйста, напишите ваш вопрос, и наш менеджер свяжется с вами в ближайшее время!"
        )
        user_id = query.from_user.id
        user_states[user_id] = "awaiting_request"  

    user_id = query.from_user.id
    if query.data == "promo_code":
        await query.edit_message_text(
            text="Чтобы получить промокод, оставьте отзыв в приложении доставки и пришлите нам скриншот в ответном сообщении💬\n\nМы обработаем отзыв и отправим вам приятный бонус. Обычно это занимает меньше суток."
        )
        user_states[user_id] = "awaiting_photo"
    elif query.data == "leave_request":
        await query.edit_message_text(
            text="Если у вас возникли вопросы по доставке, пожалуйста, оставьте ваше обращение в ответном сообщении. Наш менеджер в ближайшее время обязательно свяжется с вами и поможет решить все проблемы⬇️"
        )
        user_states[user_id] = "awaiting_request"

# Пересылка сообщений пользователей в группу
async def user_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global GROUP_CHAT_ID
    user = update.message.from_user
    user_id = user.id
    original_message = update.message
    try:
        # Пытаемся переслать сообщение в группу
        forwarded_message = await context.bot.forward_message(
            chat_id=GROUP_CHAT_ID,
            from_chat_id=original_message.chat.id,
            message_id=original_message.message_id,
        )

        # Сохраняем данные о пересланном сообщении
        forwarded_messages[forwarded_message.message_id] = {
            "user_id": user_id,
            "original_message_id": original_message.message_id,
        }
        await update.message.reply_text("Ваше сообщение отправлено менеджеру.")

    except ChatMigrated as e:
        # Обработка миграции группы в супергруппу
        GROUP_CHAT_ID = e.new_chat_id  # Сохраняем новый идентификатор супергруппы

        # Повторяем попытку переслать сообщение с новым идентификатором
        forwarded_message = await context.bot.forward_message(
            chat_id=GROUP_CHAT_ID,
            from_chat_id=original_message.chat.id,
            message_id=original_message.message_id,
        )

        # Сохраняем данные о пересланном сообщении
        forwarded_messages[forwarded_message.message_id] = {
            "user_id": user_id,
            "original_message_id": original_message.message_id,
        }

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

    await context.bot.send_message(chat_id=user_id, text=f"{reply_text}")
    await update.message.reply_text("Ответ доставлен пользователю.")


# Основная функция
def main():
    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_callback_query))
    application.add_handler(MessageHandler(filters.ChatType.PRIVATE & ~filters.COMMAND, user_message_handler))
    application.add_handler(MessageHandler(filters.Chat(GROUP_CHAT_ID) & ~filters.COMMAND, group_reply_handler))
    application.run_polling()

# Запуск приложения
if __name__ == "__main__":
    main()
    