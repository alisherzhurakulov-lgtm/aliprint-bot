# 🤖 Telegram Bot для типографии АлиПринт

Бот для бизнес-аккаунта @aliprintru

## 📋 Функционал

- Приветствие и меню услуг
- Контактная информация с графиком работы
- Оформление заявок через Google Form
- Скачивание прайс-листа
- Вызов менеджера с уведомлением
- Сохранение заявок в JSON файл

## 🔧 Настройка

1. В файле `bot.py` проверьте настройки:
   - `TELEGRAM_TOKEN` - токен бота
   - `MANAGER_ID` - ID менеджера для уведомлений
   - `CONTACTS` - контактные данные
   - `LINKS` - ссылки на прайс и форму

## 🚀 Деплой на Render

1. Загрузите код на GitHub
2. На [render.com](https://render.com) создайте новый Web Service
3. Подключите репозиторий
4. Настройки:
   - Environment: Python 3
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python bot.py`
5. Нажмите "Create Web Service"

## 📊 Команды

- `/start` - начать работу с ботом
- `/stats` - статистика (только для менеджера)