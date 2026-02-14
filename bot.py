#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Telegram BUSINESS Bot для типографии АлиПринт
Бот отвечает на сообщения в бизнес-аккаунте @aliprintru
"""

import logging
import json
import os
from datetime import datetime
from typing import Dict, Any

from telegram import (
    Update, 
    InlineKeyboardButton, 
    InlineKeyboardMarkup
)
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ContextTypes
)

# ======================== НАСТРОЙКИ ========================
TELEGRAM_TOKEN = "8536900751:AAHjMDyZoeRzdBKacRj7jxPSCu_RPp3EWYg"
MANAGER_ID = 860529281

# Контактная информация
CONTACTS = {
    "address": "Москва, 1-й Красногорский проезд, 4с3А, 1 этаж",
    "metro": "Ближайшие станции: МЦК Лужники, м. Спортивная, м. Фрунзенская",
    "phone": "+7 (925) 202-94-52",
    "phone_link": "+79252029452",
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

# Услуги
SERVICES = {
    "operativnaya": {
        "name": "📄 Оперативная полиграфия",
        "items": ["Визитки", "Листовки", "Буклеты", "Флаеры", "Бланки"]
    },
    "listovaya": {
        "name": "📋 Листовая печать",
        "items": ["Чертежи", "Плакаты", "Постеры", "Техническая документация"]
    },
    "shirokoformatnaya": {
        "name": "🖼 Широкоформатная печать",
        "items": ["Баннеры", "Роллапы", "Лайтбоксы", "Интерьерная печать", "Пленка"]
    },
    "suveniry": {
        "name": "🎁 Сувениры",
        "items": ["Кружки", "Футболки", "Блокноты", "Ручки с логотипом", "Магниты"]
    },
    "dtf": {
        "name": "👕 DTF печать на текстиле",
        "items": ["Термотрансфер", "Печать на футболках", "Печать на толстовках", "Печать на спецодежде"]
    }
}

REQUESTS_FILE = "requests.json"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
# ============================================================

def get_main_keyboard():
    """Возвращает клавиатуру главного меню"""
    keyboard = [
        [InlineKeyboardButton("📋 Наши услуги", callback_data="services")],
        [InlineKeyboardButton("📞 Контакты", callback_data="contacts"),
         InlineKeyboardButton("📝 Оставить заявку", callback_data="order")],
        [InlineKeyboardButton("📎 Скачать прайс-лист", callback_data="price"),
         InlineKeyboardButton("👤 Позвать менеджера", callback_data="call_manager")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ======================== ОБРАБОТЧИКИ ========================

async def business_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    ГЛАВНЫЙ ОБРАБОТЧИК для сообщений в бизнес-аккаунте!
    Срабатывает, когда клиент пишет в @aliprintru
    """
    business_connection = update.business_connection
    message = update.business_message
    
    # Проверяем, что сообщение от клиента (не от владельца)
    if message.from_user.id != business_connection.user.id:
        logger.info(f"Сообщение в бизнес-аккаунт от @{message.from_user.username}: {message.text}")
        
        # Приветственное сообщение
        welcome_text = (
            f"👋 Здравствуйте! Это типография *АлиПринт*.\n\n"
            f"{CONTACTS['working_hours']}\n\n"
            f"📍 {CONTACTS['address']}\n"
            f"🚇 {CONTACTS['metro']}\n\n"
            f"Чем мы можем вам помочь? Выберите действие:"
        )
        
        # Отправляем ответ (он придет от имени @aliprintru)
        await message.reply_text(
            welcome_text,
            reply_markup=get_main_keyboard(),
            parse_mode='Markdown'
        )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start (когда пишут боту напрямую)"""
    welcome_text = (
        f"👋 Рады вам в нашей коммерческой типографии *АлиПринт*!\n\n"
        f"{CONTACTS['working_hours']}\n\n"
        f"📍 {CONTACTS['address']}\n"
        f"🚇 {CONTACTS['metro']}\n\n"
        f"Выберите нужное действие:"
    )
    
    await update.message.reply_text(
        welcome_text,
        reply_markup=get_main_keyboard(),
        parse_mode='Markdown'
    )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик нажатий на кнопки"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "services":
        await show_services(query)
    elif query.data == "contacts":
        await show_contacts(query)
    elif query.data == "order":
        await create_order(query, context)
    elif query.data == "price":
        await send_price(query)
    elif query.data == "call_manager":
        await call_manager(query, context)
    elif query.data.startswith("service_"):
        await show_service_detail(query)
    elif query.data == "back_to_main":
        await back_to_main(query)

async def show_services(query) -> None:
    """Показывает меню услуг"""
    keyboard = []
    for service_key, service_data in SERVICES.items():
        keyboard.append([InlineKeyboardButton(
            service_data["name"], 
            callback_data=f"service_{service_key}"
        )])
    
    keyboard.append([InlineKeyboardButton("◀️ На главную", callback_data="back_to_main")])
    
    await query.edit_message_text(
        "📋 *Наши услуги:*\n\nВыберите раздел:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def show_service_detail(query) -> None:
    """Показывает детали услуги"""
    service_key = query.data.replace("service_", "")
    service_data = SERVICES.get(service_key, {})
    
    items_list = "\n".join([f"• {item}" for item in service_data["items"]])
    text = f"*{service_data['name']}*\n\n{items_list}\n\n📍 Для заказа нажмите кнопку ниже:"
    
    keyboard = [
        [InlineKeyboardButton("📝 Оставить заявку", callback_data="order")],
        [InlineKeyboardButton("◀️ К услугам", callback_data="services"),
         InlineKeyboardButton("🏠 На главную", callback_data="back_to_main")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def show_contacts(query) -> None:
    """Показывает контакты"""
    text = (
        f"*Наши контакты:*\n\n"
        f"🏢 {CONTACTS['address']}\n"
        f"🚇 {CONTACTS['metro']}\n\n"
        f"📞 {CONTACTS['phone']}\n"
        f"⏰ {CONTACTS['working_hours']}\n"
        f"💬 @aliprintru"
    )
    
    keyboard = [
        [InlineKeyboardButton("📞 Позвонить", url=f"tel:{CONTACTS['phone_link']}")],
        [InlineKeyboardButton("◀️ На главную", callback_data="back_to_main")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def create_order(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка заявки"""
    user = query.from_user
    
    # Уведомление менеджеру
    try:
        manager_text = (
            f"🔔 *Новая заявка!*\n\n"
            f"👤 Пользователь: {user.first_name} {user.last_name or ''}\n"
            f"📱 Username: @{user.username or 'не указан'}\n"
            f"⏰ {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        )
        await context.bot.send_message(chat_id=MANAGER_ID, text=manager_text, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Ошибка уведомления: {e}")
    
    text = f"📝 *Заполните форму*\n\n[Открыть форму заказа]({LINKS['order_form']})"
    
    keyboard = [
        [InlineKeyboardButton("📝 Перейти к форме", url=LINKS['order_form'])],
        [InlineKeyboardButton("◀️ На главную", callback_data="back_to_main")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def send_price(query) -> None:
    """Отправка прайса"""
    text = f"📎 *Прайс-лист*\n\n[Открыть прайс-лист]({LINKS['price']})"
    
    keyboard = [
        [InlineKeyboardButton("📎 Открыть", url=LINKS['price'])],
        [InlineKeyboardButton("◀️ На главную", callback_data="back_to_main")]
    ]
    
    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

async def call_manager(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Вызов менеджера"""
    user = query.from_user
    
    try:
        manager_text = (
            f"🚨 *СРОЧНЫЙ ВЫЗОВ!*\n\n"
            f"👤 {user.first_name} @{user.username}\n"
            f"👉 [Ответить](tg://user?id={user.id})"
        )
        await context.bot.send_message(chat_id=MANAGER_ID, text=manager_text, parse_mode='Markdown')
        
        await query.edit_message_text(
            "✅ *Менеджер вызван!*\n\nСкоро свяжемся!",
            parse_mode='Markdown'
        )
    except:
        await query.edit_message_text("❌ Ошибка вызова")
    
    import asyncio
    await asyncio.sleep(2)
    await back_to_main(query)

async def back_to_main(query) -> None:
    """Возврат в главное меню"""
    await query.edit_message_text(
        "👋 *Главное меню*\n\nВыберите действие:",
        reply_markup=get_main_keyboard(),
        parse_mode='Markdown'
    )

# ======================== ЗАПУСК ========================

def main() -> None:
    """Запуск бота"""
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Регистрируем обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # ГЛАВНЫЙ ОБРАБОТЧИК ДЛЯ BUSINESS! - ИСПРАВЛЕНО
    application.add_handler(MessageHandler(
        filters.StatusUpdate.BUSINESS_MESSAGE,  # <- ВОТ ПРАВИЛЬНОЕ НАЗВАНИЕ!
        business_message
    ))
    
    logger.info("🚀 BUSINESS бот запущен и ждет сообщения в @aliprintru")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()


