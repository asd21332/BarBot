from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
import sqlite3

# Подключение к базе данных
def get_db_connection():
    conn = sqlite3.connect('drinks.db')
    conn.row_factory = sqlite3.Row
    return conn

# Создание постоянной клавиатуры с кнопкой "МЕНЮ"
def get_menu_keyboard():
    keyboard = [['МЕНЮ']]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)

# Команда /start: Показать категории
async def start(update: Update, context):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Categories')
        categories = cursor.fetchall()

    keyboard = [[InlineKeyboardButton(cat['category_name'], callback_data=f'category_{cat["category_id"]}')] 
                for cat in categories]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('Выберите категорию:', reply_markup=reply_markup)

# Обработка выбора категории: Показать напитки
async def handle_category(update: Update, context):
    query = update.callback_query
    await query.answer()
    category_id = query.data.split('_')[1]
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Drinks WHERE category_id = ?', (category_id,))
        drinks = cursor.fetchall()

    keyboard = [[InlineKeyboardButton(drink['name'], callback_data=f'drink_{drink["drink_id"]}')] 
                for drink in drinks]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await query.message.reply_text('Выберите напиток:', reply_markup=reply_markup)

# Обработка выбора напитка: Показать рецепт и картинку
async def handle_drink(update: Update, context):
    query = update.callback_query
    await query.answer()
    drink_id = query.data.split('_')[1]
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Drinks WHERE drink_id = ?', (drink_id,))
        drink = cursor.fetchone()

    # Разделяем рецепт на строки по запятым и создаем форматированный текст
    recipe_lines = drink['recipe'].split(',')
    formatted_recipe = '\n'.join([f"• {line.strip()}" for line in recipe_lines])
    
    # Формируем сообщение с жирным названием в HTML
    message = f"<b>{drink['name']}</b>\n\n{formatted_recipe}"
    
    # Отправляем сообщение с рецептом
    await query.message.reply_text(message, parse_mode='HTML')
    
    # Отправляем изображение
    try:
        await query.message.reply_photo(photo=drink['image_url'], reply_markup=get_menu_keyboard())
    except Exception as e:
        await query.message.reply_text(f"Ошибка при отправке изображения: {e}", reply_markup=get_menu_keyboard())

# Функция поиска: Обработка текстового ввода
async def search(update: Update, context):
    search_term = update.message.text
    if search_term == 'МЕНЮ':
        await start(update, context)  # Вызываем start при нажатии кнопки "МЕНЮ"
        return

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM Drinks WHERE LOWER(name) LIKE LOWER(?)', (f'%{search_term}%',))
        drinks = cursor.fetchall()

    if drinks:
        keyboard = [[InlineKeyboardButton(drink['name'], callback_data=f'drink_{drink["drink_id"]}')] 
                    for drink in drinks]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text('Найденные напитки:', reply_markup=reply_markup)
    else:
        await update.message.reply_text('Напитков не найдено.', reply_markup=get_menu_keyboard())

# Основная функция для запуска бота
def main():
    print("Запуск бота...")
    # Замените 'YOUR_BOT_API_TOKEN' на ваш токен от BotFather
    application = Application.builder().token('TOKEN').build()

    # Добавление обработчиков
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CallbackQueryHandler(handle_category, pattern='^category_'))
    application.add_handler(CallbackQueryHandler(handle_drink, pattern='^drink_'))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, search))

    print("Обработчики добавлены, начинаю polling...")
    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    main()
