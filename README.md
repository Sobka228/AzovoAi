

# <img width="359" height="114" alt="ascii-art-text" src="https://github.com/user-attachments/assets/e46502f8-c7f5-4702-a57a-6675b22475dc" />

[![Telegram](https://img.shields.io/badge/Telegram-@azovoAIbot-0088cc?style=plastic&logo=telegram)](https://t.me/azovoAIbot)
[![Python](https://img.shields.io/badge/Python-3.10+-3776ab?style=plastic&logo=python)](https://python.org)
[![Render](https://img.shields.io/badge/Render-Deployed-46e3b7?style=plastic&logo=render)](https://render.com)
[![Website](https://img.shields.io/badge/Website-azovo.xo.je-FF6B6B?style=plastic&logo=googlechrome&logoColor=white)](https://azovo.xo.je)

```bash
# 1. Клонируйте репо
git clone https://github.com/YOUR_USERNAME/azovoai.git
cd azovoai

# 2. Установите зависимости
pip install -r requirements.txt

# 3. Создайте .env
cp .env.example .env
# Отредактируйте .env и добавьте BOT_TOKEN от @BotFather

# 4. Запустите
python main.py
```

## Возможности

- Telegram API интеграция (aiogram 3.4.1)
- Pollinations.ai API (free, no auth)
- Queue система для обработки сообщений
- Rate limiting
- Emoji реакции на сообщения
- Планировщик автосообщений
- Чёрный список пользователей
- Статистика и мониторинг
- 15+ админ команд
- Датасет для обучения

## Требования

- Python 3.8+
- Интернет подключение
- Telegram bot token от @BotFather

## Установка

Смотри [INSTALL.md](INSTALL.md)

## 📖 Документация

- **[INSTALL.md](INSTALL.md)** — Установка и первый запуск
- **[COMMANDS.md](COMMANDS.md)** — Все команды бота
- **[TUTORIAL.md](TUTORIAL.md)** — Пошаговый туториал
- **[CUSTOMIZE.md](CUSTOMIZE.md)** — Кастомизация поведения
- **[API.md](API.md)** — Информация об API
- **[DEPLOY.md](DEPLOY.md)** — Развёртывание на Render

## Развёртывание

### Локально (на операционках типо линукс и виндовс даже на термуксе можно)
```bash
python main.py
```

### На Render (24/7 бесплатно)
Смотри [DEPLOY.md](DEPLOY.md)

## Основные команды

```
/ping              - Статус и пинг
/bot               - Статистика
/reset             - Сбросить очередь
/dataset_stats     - Статистика датасета
/thoughts_start    - Автосообщения
/thoughts_stop     - Остановить
```

Полный список: [COMMANDS.md](COMMANDS.md)

## Конфигурация

`.env` переменные:
- `BOT_TOKEN` — Telegram bot token (обязательно)
- `BOT_USERNAME` — Имя бота в Telegram
- `ADMIN_USER_ID` — ID админа
- `POLLINATIONS_MODEL` — Модель AI (default: openai)
- `RATE_LIMIT_SECONDS` — Задержка между ответами (default: 2)

## Структура проекта

```
.
├── main.py                # Основной код
├── requirements.txt       # Зависимости
├── .env.example          # Шаблон переменных
├── check_setup.py        # Проверка настройки
├── run.bat               # Запуск для Windows
│
├── dataset.txt           # Датасет для обучения
├── bot_stats.json        # Статистика
├── blacklist.json        # Чёрный список
├── user_consent.json     # Согласия
└── bot_chats.json        # История чатов
```

## Как это работает

1. Сообщение от пользователя → очередь
2. Проверка триггеров (азово, @бот_имя)
3. Отправка на Pollinations.ai API
4. GPT-4o-mini обрабатывает
5. Ответ отправляется в Telegram
6. Данные сохраняются в датасет

## Безопасность

- Чёрный список блокирует хуйню
- Rate limiting защищает от флуда
- Логирование всех событий
- BOT_TOKEN в .env

## Статистика

Бот автоматически собирает:
- Количество сообщений
- Активных пользователей
- Время работы
- История сообщений

Команда `/bot` показывает всё.

## Разработка

```bash
# Проверить настройку
python check_setup.py

# Логи в консоли при запуске
python main.py

# Найти ошибки
grep -r "error\|Error\|ERROR" main.py
```

## 💬 Контакты

Telegram: [@azovoAIbot](https://t.me/azovoAIbot)

---

