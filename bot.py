#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Telegram Bot для типографии АлиПринт
Бот для бизнес-аккаунта @aliprintru
"""

import logging
import json
import os
from datetime import datetime
from typing import Dict, Any

from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)

# ======================== НАСТРОЙКИ (ИЗМЕНИТЕ ПОД СЕБЯ) ========================
TELEGRAM_TOKEN = "8418731158:AAHv-xLv6ul5nJJJUspSI9Qrx-UjIBJk5TQ"  # Токен бота
MANAGER_ID = 860529281  # ID менеджера для уведомлений

# Контактная информация
CONTACTS = {
    "address": "Москва, 1-й Красногорский проезд, 4с3А, 1 этаж",
    "metro": "Ближайшие станции: МЦК Лужники, м. Спортивная, м. Фрунзенская",
    "phone": "+7 (925) 202-94-52",
    "phone_link": "+79252029452",  # для ссылки
    "working_hours": """
График работы:
Пн-Вт: 12:00 - 19:00
Ср-Пт: 09:00 - 19:00
Сб-Вс: 09:00 - 15:00
    """.strip()
}

# Ссылки
LINKS = {
    "price": "https://docs.google.com/spreadsheets/d/1UYrBDY3Xy_olCsQW9E6P3zxFuq7FTkzatJXW9WdD2oA/edit?usp=sharing",
    "order_form": "https://docs.google.com/forms/d/e/1FAIpQLScxoroyah632vx9Qea8YEJMXBtP28ucqPGnQtv7EHMaDf79Fw/viewform?usp=dialog"
}

# Услуги типографии (для меню)
SERVICES = {
    "operativnaya": {
        "name": "📄 Оперативная полиграфия",
        "items": [
            "Визитки",
            "Листовки",
            "Буклеты",
            "Флаеры",
            "Бланки"
        ]
    },
    "listovaya": {
        "name": "📋 Листовая печать",
        "items": [
            "Чертежи",
            "Плакаты",
            "Постеры",
            "Техническая документация"
        ]
    },
    "shirokoformatnaya": {
        "name": "🖼 Широкоформатная печать",
        "items": [
            "Баннеры",
            "Роллапы",
            "Лайтбоксы",
            "Интерьерная печать",
            "Пленка"
        ]
    },
    "suveniry": {
        "name": "🎁 Сувениры",
        "items": [
            "Кружки",
            "Футболки",
            "Блокноты",
            "Ручки с логотипом",
            "Магниты"
        ]
    },
    "dtf": {
        "name": "👕 DTF печать на текстиле",
        "items": [
            "Термотрансфер",
            "Печать на футболках",
            "Печать на толстовках",
            "Печать на спецодежде"
        ]
    }
}

# Имя файла для хранения заявок (не требует БД)
REQUESTS_FILE = "requests.json"

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
# ========================================================================


# ======================== РАБОТА С ФАЙЛОМ ЗАЯВОК ========================
def save_request(user_data: Dict[str, Any]) -> None:
    """Сохраняет заявку в JSON файл"""
    try:
        # Создаем файл если его нет
        if not os.path.exists(REQUESTS_FILE):
            with open(REQUESTS_FILE, 'w', encoding='utf-8') as f:
                json.dump([], f)
        
        # Читаем существующие заявки
        with open(REQUESTS_FILE, 'r', encoding='utf-8') as f:
            requests = json.load(f)
        
        # Добавляем новую заявку
        requests.append(user_data)
        
        # Сохраняем обратно
        with open(REQUESTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(requests, f, ensure_ascii=False, indent=2)
            
    except Exception as e:
        logger.error(f"Ошибка при сохранении заявки: {e}")


def get_requests_count() -> int:
    """Возвращает количество заявок"""
    try:
        if os.path.exists(REQUESTS_FILE):
            with open(REQUESTS_FILE, 'r', encoding='utf-8') as f:
                return len(json.load(f))
        return 0
    except:
        return 0
# ========================================================================


# ======================== ОСНОВНЫЕ ФУНКЦИИ БОТА ========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    user = update.effective_user
    
    # Приветственное сообщение
    welcome_text = (
        f"👋 Рады вам в нашей коммерческой типографии *АлиПринт*!\n\n"
        f"{CONTACTS['working_hours']}\n\n"
        f"📍 {CONTACTS['address']}\n"
        f"🚇 {CONTACTS['metro']}\n\n"
        f"Выберите нужное действие:"
    )
    
    # Создаем клавиатуру
    keyboard = [
        [InlineKeyboardButton("📋 Наши услуги", callback_data="services")],
        [InlineKeyboardButton("📞 Контакты", callback_data="contacts"),
         InlineKeyboardButton("📝 Оставить заявку", callback_data="order")],
        [InlineKeyboardButton("📎 Скачать прайс-лист", callback_data="price"),
         InlineKeyboardButton("👤 Позвать менеджера", callback_data="call_manager")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Отправляем сообщение
    await update.message.reply_text(
        welcome_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )
    
    # Логируем запуск
    logger.info(f"Пользователь {user.first_name} (@{user.username}) запустил бота")


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик нажатий на кнопки"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "services":
        await show_services_menu(query)
    
    elif query.data == "contacts":
        await show_contacts(query)
    
    elif query.data == "order":
        await create_order(query, context)
    
    elif query.data == "price":
        await send_price(query)
    
    elif query.data == "call_manager":
        await call_manager(query, context)
    
    elif query.data.startswith("service_"):
        await show_service_details(query)
    
    elif query.data == "back_to_main":
        await back_to_main(query)


async def show_services_menu(query) -> None:
    """Показывает меню услуг"""
    keyboard = []
    
    # Добавляем кнопки для каждого раздела услуг
    for service_key, service_data in SERVICES.items():
        keyboard.append([InlineKeyboardButton(
            service_data["name"], 
            callback_data=f"service_{service_key}"
        )])
    
    # Кнопка "Назад"
    keyboard.append([InlineKeyboardButton("◀️ На главную", callback_data="back_to_main")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        "📋 *Наши услуги:*\n\nВыберите интересующий раздел:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def show_service_details(query) -> None:
    """Показывает детали конкретной услуги"""
    service_key = query.data.replace("service_", "")
    service_data = SERVICES.get(service_key, {})
    
    if service_data:
        items_list = "\n".join([f"• {item}" for item in service_data["items"]])
        text = f"*{service_data['name']}*\n\n{items_list}\n\n📍 Для заказа нажмите кнопку ниже:"
        
        keyboard = [
            [InlineKeyboardButton("📝 Оставить заявку", callback_data="order")],
            [InlineKeyboardButton("◀️ К услугам", callback_data="services"),
             InlineKeyboardButton("🏠 На главную", callback_data="back_to_main")]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )


async def show_contacts(query) -> None:
    """Показывает контактную информацию"""
    contacts_text = (
        f"*Наши контакты:*\n\n"
        f"🏢 {CONTACTS['address']}\n"
        f"🚇 {CONTACTS['metro']}\n\n"
        f"📞 {CONTACTS['phone']}\n"
        f"⏰ {CONTACTS['working_hours']}\n\n"
        f"💬 *Telegram:* @aliprintru\n"
        f"📧 Почта: info@aliprint.ru\n\n"
        f"🔗 [Перейти на сайт](https://aliprint.ru)"
    )
    
    keyboard = [
        [InlineKeyboardButton("📞 Позвонить", url=f"tel:{CONTACTS['phone_link']}")],
        [InlineKeyboardButton("💬 Написать в Telegram", url="https://t.me/aliprintru")],
        [InlineKeyboardButton("◀️ На главную", callback_data="back_to_main")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        contacts_text,
        reply_markup=reply_markup,
        parse_mode='Markdown',
        disable_web_page_preview=True
    )


async def create_order(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Создание заявки через Google Form"""
    user = query.from_user
    
    # Сохраняем информацию о заявке
    order_data = {
        "user_id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "timestamp": datetime.now().isoformat()
    }
    save_request(order_data)
    
    # Отправляем уведомление менеджеру
    try:
        manager_message = (
            f"🔔 *Новая заявка!*\n\n"
            f"👤 Пользователь: {user.first_name} {user.last_name or ''}\n"
            f"🆔 ID: {user.id}\n"
            f"📱 Username: @{user.username or 'не указан'}\n"
            f"⏰ Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
            f"Пользователь открыл форму для заказа."
        )
        
        await context.bot.send_message(
            chat_id=MANAGER_ID,
            text=manager_message,
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Не удалось отправить уведомление менеджеру: {e}")
    
    # Отправляем пользователю ссылку на форму
    order_text = (
        f"📝 *Оформление заказа*\n\n"
        f"Для оформления заказа заполните форму:\n\n"
        f"[Открыть форму заказа]({LINKS['order_form']})\n\n"
        f"✅ После заполнения наш менеджер свяжется с вами в ближайшее время!"
    )
    
    keyboard = [
        [InlineKeyboardButton("📝 Перейти к форме", url=LINKS['order_form'])],
        [InlineKeyboardButton("◀️ На главную", callback_data="back_to_main")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        order_text,
        reply_markup=reply_markup,
        parse_mode='Markdown',
        disable_web_page_preview=True
    )


async def send_price(query) -> None:
    """Отправляет ссылку на прайс-лист"""
    price_text = (
        f"📎 *Прайс-лист*\n\n"
        f"Скачайте актуальный прайс-лист по ссылке ниже:\n\n"
        f"[Открыть прайс-лист]({LINKS['price']})\n\n"
        f"✅ Файл откроется в Google Таблицах"
    )
    
    keyboard = [
        [InlineKeyboardButton("📎 Открыть прайс-лист", url=LINKS['price'])],
        [InlineKeyboardButton("◀️ На главную", callback_data="back_to_main")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await query.edit_message_text(
        price_text,
        reply_markup=reply_markup,
        parse_mode='Markdown',
        disable_web_page_preview=True
    )


async def call_manager(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Вызов менеджера"""
    user = query.from_user
    
    # Уведомление менеджеру
    try:
        manager_message = (
            f"🚨 *СРОЧНЫЙ ВЫЗОВ МЕНЕДЖЕРА!*\n\n"
            f"👤 Пользователь: {user.first_name} {user.last_name or ''}\n"
            f"🆔 ID: {user.id}\n"
            f"📱 Username: @{user.username or 'не указан'}\n"
            f"⏰ Время: {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
            f"👉 [Написать пользователю](tg://user?id={user.id})"
        )
        
        await context.bot.send_message(
            chat_id=MANAGER_ID,
            text=manager_message,
            parse_mode='Markdown'
        )
        
        # Подтверждение пользователю
        await query.edit_message_text(
            "✅ *Менеджер вызван!*\n\n"
            "Специалист свяжется с вами в ближайшее время.\n\n"
            "Спасибо за обращение в АлиПринт!",
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"Ошибка при вызове менеджера: {e}")
        await query.edit_message_text(
            "❌ Произошла ошибка при вызове менеджера.\n"
            "Пожалуйста, попробуйте позже или свяжитесь с нами по телефону.",
            parse_mode='Markdown'
        )
    
    # Даем небольшую паузу и возвращаем в главное меню
    import asyncio
    await asyncio.sleep(3)
    await back_to_main(query)


async def back_to_main(query) -> None:
    """Возврат в главное меню"""
    keyboard = [
        [InlineKeyboardButton("📋 Наши услуги", callback_data="services")],
        [InlineKeyboardButton("📞 Контакты", callback_data="contacts"),
         InlineKeyboardButton("📝 Оставить заявку", callback_data="order")],
        [InlineKeyboardButton("📎 Скачать прайс-лист", callback_data="price"),
         InlineKeyboardButton("👤 Позвать менеджера", callback_data="call_manager")]
    ]
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    main_text = (
        f"👋 *Главное меню*\n\n"
        f"Выберите нужное действие:"
    )
    
    await query.edit_message_text(
        main_text,
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик обычных сообщений"""
    # Если пользователь пишет что-то, предлагаем воспользоваться меню
    await update.message.reply_text(
        "Используйте кнопки меню для навигации 👇",
        reply_markup=InlineKeyboardMarkup([[
            InlineKeyboardButton("🏠 Открыть меню", callback_data="back_to_main")
        ]])
    )


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Секретная команда /stats для просмотра статистики (только для менеджера)"""
    user = update.effective_user
    
    if user.id == MANAGER_ID:
        requests_count = get_requests_count()
        await update.message.reply_text(
            f"📊 *Статистика*\n\n"
            f"Всего заявок: {requests_count}\n\n"
            f"Бот работает нормально ✅",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text("❌ У вас нет прав для этой команды")
# ========================================================================


# ======================== ЗАПУСК БОТА ========================
def main() -> None:
    """Главная функция запуска бота"""
    
    # Проверяем наличие токена
    if not TELEGRAM_TOKEN:
        logger.error("Не указан TELEGRAM_TOKEN!")
        return
    
    # Создаем приложение
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Запускаем бота
    logger.info("Бот запущен и готов к работе!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == '__main__':
    main()

# ========================================================================
