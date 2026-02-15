#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Telegram BUSINESS Bot для типографии АлиПринт
Бот отвечает на сообщения в бизнес-аккаунте @aliprintru
Версия: Умный автоответчик (1 раз в 12 часов на пользователя) + Самопинг
"""

import logging
import json
import os
import time
import asyncio
from datetime import datetime, timedelta
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
TELEGRAM_TOKEN = "8418731158:AAHv-xLv6ul5nJJJUspSI9Qrx-UjIBJk5TQ"
MANAGER_ID = 860529281

# Контактная информация
CONTACTS = {
    "address": "Москва, 1-й Красногорский проезд, 4с3А, 1 этаж",
    "metro": "Ближайшие станции: МЦК Стрешнево, м. Сокол, м. Войковская",
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
RESPONSES_FILE = "responses.json"  # Файл для хранения истории ответов

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
# ============================================================

# ======================== РАБОТА С ФАЙЛАМИ ========================

def load_responses():
    """Загружает историю ответов из файла"""
    if os.path.exists(RESPONSES_FILE):
        try:
            with open(RESPONSES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Ошибка загрузки истории ответов: {e}")
            return {}
    return {}

def save_responses(data):
    """Сохраняет историю ответов в файл"""
    try:
        with open(RESPONSES_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Ошибка сохранения истории ответов: {e}")

def save_request(user_data: Dict[str, Any]) -> None:
    """Сохраняет заявку в JSON файл"""
    try:
        if not os.path.exists(REQUESTS_FILE):
            with open(REQUESTS_FILE, 'w', encoding='utf-8') as f:
                json.dump([], f)
        
        with open(REQUESTS_FILE, 'r', encoding='utf-8') as f:
            requests = json.load(f)
        
        requests.append(user_data)
        
        with open(REQUESTS_FILE, 'w', encoding='utf-8') as f:
            json.dump(requests, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Ошибка при сохранении заявки: {e}")

# Загружаем историю при старте
user_response_history = load_responses()
# Словарь для блокировок (защита от одновременных сообщений)
response_locks = {}
# Словарь для отслеживания напоминаний
last_reminder = {}
# ============================================================

def get_main_keyboard():
    """Возвращает клавиатуру главного меню"""
    keyboard = [
        [InlineKeyboardButton("📋 Наши услуги", callback_data="services")],
        [InlineKeyboardButton("📞 Контакты", callback_data="contacts"),
         InlineKeyboardButton("📝 Оставить заявку", callback_data="order")],
        [InlineKeyboardButton("📎 Скачать прайс-лист", callback_data="price"),
         InlineKeyboardButton("👤 Позвать менеджера", callback_data="call_manager")],
        [InlineKeyboardButton("🤝 Связаться с менеджером", callback_data="human")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ======================== САМОПИНГ ========================

async def ping_self(context: ContextTypes.DEFAULT_TYPE):
    """Пинг самого себя каждые 10 минут, чтобы Render не усыпил"""
    try:
        logger.info(f"🏓 Самопинг: бот активен, обработано диалогов: {len(user_response_history)}")
        # Просто логируем активность - этого достаточно для самопинга
    except Exception as e:
        logger.error(f"❌ Ошибка самопинга: {e}")

# ======================== ОБРАБОТЧИКИ ========================

async def business_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Умный обработчик для сообщений в бизнес-аккаунте:
    - Отвечает только на первое сообщение в диалоге
    - Не чаще чем раз в 12 часов для каждого пользователя
    - С блокировкой для защиты от одновременных сообщений
    """
    try:
        message = update.business_message
        user_id = str(message.from_user.id)
        current_time = time.time()
        
        logger.info(f"📨 Получено business сообщение от @{message.from_user.username}: {message.text}")
        
        # Создаем блокировку для пользователя, если её нет
        if user_id not in response_locks:
            response_locks[user_id] = asyncio.Lock()
        
        # Используем блокировку для предотвращения одновременных ответов
        async with response_locks[user_id]:
            # Проверяем историю ответов
            last_response = user_response_history.get(user_id, 0)
            time_since_last = current_time - last_response
            
            # 12 часов = 43200 секунд
            if time_since_last < 43200:
                hours_left = int((43200 - time_since_last) / 3600)
                minutes_left = int(((43200 - time_since_last) % 3600) / 60)
                logger.info(f"⏳ Пользователю @{message.from_user.username} уже отвечали. Следующий автоответ через {hours_left}ч {minutes_left}м")
                
                # Если прошло больше часа и не отправляли напоминание в последний час
                if 3600 < time_since_last < 43200:
                    last_remind = last_reminder.get(user_id, 0)
                    if current_time - last_remind > 3600:  # Не чаще раза в час
                        await message.reply_text(
                            f"🕒 Напоминаем: мы уже отвечали вам сегодня. Если нужна помощь специалиста, нажмите кнопку «Позвать менеджера».",
                            reply_markup=get_main_keyboard()
                        )
                        last_reminder[user_id] = current_time
                        logger.info(f"💬 Отправлено напоминание @{message.from_user.username}")
                return
            
            # Отправляем приветствие (первый раз за 12 часов)
            welcome_text = (
                f"👋 Здравствуйте! Это типография *АлиПринт*.\n\n"
                f"⏰ {CONTACTS['working_hours']}\n"
                f"📍 {CONTACTS['address']}\n"
                f"🚇 {CONTACTS['metro']}\n\n"
                f"📌 *Это автоматическое сообщение (1 раз в 12 часов)*\n"
                f"Если нужна помощь специалиста — нажмите кнопку «Позвать менеджера».\n\n"
                f"Чем мы можем вам помочь?"
            )
            
            await message.reply_text(
                welcome_text,
                reply_markup=get_main_keyboard(),
                parse_mode='Markdown'
            )
            
            # Запоминаем время ответа
            user_response_history[user_id] = current_time
            save_responses(user_response_history)
            
            # Ограничиваем размер истории (оставляем последние 1000 записей)
            if len(user_response_history) > 1000:
                # Сортируем по времени и оставляем самые свежие
                sorted_items = sorted(user_response_history.items(), key=lambda x: x[1], reverse=True)[:1000]
                user_response_history.clear()
                user_response_history.update(dict(sorted_items))
                save_responses(user_response_history)
            
            logger.info(f"✅ Отправлен автоответ @{message.from_user.username} (следующий через 12ч)")
        
    except Exception as e:
        logger.error(f"❌ Ошибка в business_message: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик команды /start"""
    try:
        welcome_text = (
            f"👋 Рады вам в нашей коммерческой типографии *АлиПринт*!\n\n"
            f"⏰ {CONTACTS['working_hours']}\n\n"
            f"📍 {CONTACTS['address']}\n"
            f"🚇 {CONTACTS['metro']}\n\n"
            f"Выберите нужное действие:"
        )
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=get_main_keyboard(),
            parse_mode='Markdown'
        )
        logger.info(f"✅ Ответ на /start отправлен пользователю @{update.effective_user.username}")
    except Exception as e:
        logger.error(f"❌ Ошибка в start: {e}")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик нажатий на кнопки"""
    query = update.callback_query
    await query.answer()
    
    try:
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
        elif query.data == "human":
            await connect_with_human(query, context)
        elif query.data.startswith("service_"):
            await show_service_detail(query)
        elif query.data == "back_to_main":
            await back_to_main(query)
    except Exception as e:
        logger.error(f"❌ Ошибка в button_callback: {e}")

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
    
    # Сохраняем заявку
    order_data = {
        "user_id": user.id,
        "username": user.username,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "timestamp": datetime.now().isoformat()
    }
    save_request(order_data)
    
    # Уведомление менеджеру
    try:
        manager_text = (
            f"🔔 *Новая заявка!*\n\n"
            f"👤 Пользователь: {user.first_name} {user.last_name or ''}\n"
            f"📱 Username: @{user.username or 'не указан'}\n"
            f"🆔 ID: {user.id}\n"
            f"⏰ {datetime.now().strftime('%d.%m.%Y %H:%M')}"
        )
        await context.bot.send_message(chat_id=MANAGER_ID, text=manager_text, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"❌ Ошибка уведомления менеджера: {e}")
    
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
            f"🚨 *СРОЧНЫЙ ВЫЗОВ МЕНЕДЖЕРА!*\n\n"
            f"👤 Имя: {user.first_name} {user.last_name or ''}\n"
            f"📱 Username: @{user.username or 'не указан'}\n"
            f"🆔 ID: {user.id}\n"
            f"⏰ {datetime.now().strftime('%d.%m.%Y %H:%M')}\n"
            f"👉 [Написать пользователю](tg://user?id={user.id})"
        )
        await context.bot.send_message(chat_id=MANAGER_ID, text=manager_text, parse_mode='Markdown')
        
        await query.edit_message_text(
            "✅ *Менеджер вызван!*\n\nСкоро свяжемся!",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"❌ Ошибка вызова менеджера: {e}")
        await query.edit_message_text("❌ Ошибка вызова менеджера")
    
    await asyncio.sleep(2)
    await back_to_main(query)

async def connect_with_human(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Связь с живым менеджером"""
    user = query.from_user
    user_id = str(user.id)
    
    # Удаляем пользователя из истории автоответов
    if user_id in user_response_history:
        del user_response_history[user_id]
        save_responses(user_response_history)
        logger.info(f"👤 Пользователь @{user.username} отключил автоответ")
    
    # Уведомление менеджеру
    try:
        manager_text = (
            f"🤝 *ЗАПРОС НА ЖИВОЕ ОБЩЕНИЕ*\n\n"
            f"👤 Пользователь: {user.first_name} {user.last_name or ''}\n"
            f"📱 Username: @{user.username or 'не указан'}\n"
            f"🆔 ID: {user.id}\n"
            f"⏰ {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
            f"Пользователь хочет общаться с живым менеджером. Автоответ для него отключен."
        )
        await context.bot.send_message(chat_id=MANAGER_ID, text=manager_text, parse_mode='Markdown')
        
        await query.edit_message_text(
            "✅ *Запрос передан!*\n\n"
            "Сейчас с вами свяжется живой менеджер. Ожидайте ответ в ближайшее время.\n\n"
            "Спасибо за обращение в АлиПринт!",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"❌ Ошибка при вызове менеджера: {e}")
        await query.edit_message_text("❌ Произошла ошибка. Пожалуйста, попробуйте позже.")

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
    try:
        logger.info("🚀 Запуск BUSINESS бота для @aliprintru")
        
        # Создаем приложение
        application = Application.builder().token(TELEGRAM_TOKEN).build()
        
        # Регистрируем обработчики
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CallbackQueryHandler(button_callback))
        
        # Обработчик для бизнес-сообщений
        application.add_handler(MessageHandler(
            filters.UpdateType.BUSINESS_MESSAGE,
            business_message
        ))
        
        # Добавляем самопинг каждые 10 минут (если установлен job-queue)
        if application.job_queue:
            application.job_queue.run_repeating(ping_self, interval=600, first=30)
            logger.info("⏰ Самопинг запущен (каждые 10 минут)")
        else:
            logger.warning("⚠️ JobQueue не установлен. Самопинг не работает. Установите python-telegram-bot[job-queue]")
        
        logger.info("✅ Бот успешно инициализирован, начинаем polling...")
        
        # Запускаем бота (эта функция блокирует выполнение)
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except Exception as e:
        logger.error(f"❌ Критическая ошибка при запуске бота: {e}")
        # Не завершаем процесс сразу, даем время на логи
        import time
        time.sleep(5)
        raise e

if __name__ == '__main__':
    main()
