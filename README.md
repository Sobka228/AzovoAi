

# <img width="359" height="114" alt="ascii-art-text" src="https://github.com/user-attachments/assets/e46502f8-c7f5-4702-a57a-6675b22475dc" />

[![Telegram](https://img.shields.io/badge/Telegram-@azovoAIbot-0088cc?style=plastic&logo=telegram)](https://t.me/azovoAIbot)
[![Python](https://img.shields.io/badge/Python-3.10+-3776ab?style=plastic&logo=python)](https://python.org)
[![Render](https://img.shields.io/badge/Render-Deployed-46e3b7?style=plastic&logo=render)](https://render.com)
[![Website](https://img.shields.io/badge/Website-azovo.xo.je-FF6B6B?style=plastic&logo=googlechrome&logoColor=white)](https://azovo.xo.je)


## Быстрый старт

```bash
# Клонируйте репо
git clone https://github.com/YOUR_USERNAME/azovoai.git
cd azovoai

# Установите зависимости
pip install -r requirements.txt

# Создайте .env
cp .env.example .env
# Отредактируйте .env и добавьте BOT_TOKEN от @BotFather

# Запустите
python main.py
```

## Возможности

- Telegram API интеграция (aiogram 3.4.1)
- Поддержка двух бэкендов: Pollinations.ai (облако) и Ollama (локально)
- Queue система для последовательной обработки сообщений
- Rate limiting для защиты от спама
- Реакции на сообщения эмодзи
- Автоматический планировщик сообщений
- Чёрный список пользователей
- Сбор статистики и логирование
- 15+ админ команд
- Датасет для обучения на примерах диалогов

## Требования

- Python 3.8+
- Интернет подключение
- Telegram bot token (получить от @BotFather)

## Установка

### Локально на Windows/Linux/Mac

```bash
python -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Отредактируйте .env и добавьте BOT_TOKEN
python main.py
```

## Развёртывание

### Вариант 1: На кОлокальном ПК с Pollinations.ai (облачный AI)

Самый простой вариант. Бот работает на вашем ПК, AI работает в облаке.

1. Установите зависимости:
```bash
pip install -r requirements.txt
```

2. В .env добавьте:
```
BOT_TOKEN=ваш_токен
BOT_USERNAME=имя_бота
POLLINATIONS_MODEL=openai
```

3. Запустите:
```bash
python main.py
```

Бот будет работать пока ПК включён. При отключении ПК - бот остановится.

### Вариант 2: На облаке Render (24/7 работа)

Бот работает в облаке и работает постоянно, даже если ваш ПК выключен.

#### Базовая установка:

1. Создайте репо на GitHub и запушьте код
2. Зарегистрируйтесь на render.com через GitHub
3. Создайте новый Web Service
4. Выберите ваш GitHub репо
5. Заполните поля:
   - Name: azovoai-bot
   - Environment: Python
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `python main.py`

6. Добавьте Environment Variables:
   - BOT_TOKEN = ваш_токен
   - BOT_USERNAME = имя_бота
   - POLLINATIONS_MODEL = openai
   - RATE_LIMIT_SECONDS = 2

7. Нажмите "Create Web Service"

#### Обновление кода:

Просто пушьте в GitHub, Render автоматически перезагрузит бота:

```bash
git add .
git commit -m "Update bot"
git push origin main
```

#### Логирование:

Откройте вкладку "Logs" в панели Render - там будут все события и ошибки.

#### Важно:

- Убедитесь что .env НЕ в гите (должен быть в .gitignore)
- Переменные окружения задаёте в Render dashboard
- Первый запуск может занять 1-2 минуты

### Вариант 3: Локально с Ollama (локальный AI)

AI работает на вашем ПК, полная приватность, но требует мощный компьютер.

#### Установка Ollama:

1. Скачайте Ollama с https://ollama.ai
2. Установите как обычную программу
3. Откройте терминал и скачайте модель:
```bash
ollama pull hf.co/itlwas/Vikhr-Llama-3.2-1B-Instruct-abliterated-Q4_K_M-GGUF:latest # или другой какой хотите
```

#### Запуск:

1. В одном терминале запустите Ollama сервер:
```bash
ollama serve
```

2. В другом терминале запустите бота:
```bash
python main.py
```

#### Конфигурация для Ollama:

В main.py строка ~440 замените функцию ask_ai на:

```python
def ask_ai(user_text: str) -> str:
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "mistral",
                "prompt": user_text,
                "stream": False,
                "options": {
                    "temperature": 1.2,
                    "num_predict": 100,
                    "top_p": 0.9
                }
            },
            timeout=60
        )
        if response.status_code != 200:
            return "ошибка сервера"
        return response.json()["response"].strip()
    except requests.Timeout:
        return "сервер не отвечает"
    except Exception as e:
        return f"ошибка: {e}"
```

## Основные команды

```
/ping              Проверка статуса и пинг к API
/bot               Полная статистика бота
/reset             Сбросить очередь сообщений
/queue             Текущая очередь обработки
/dataset_stats     Статистика датасета
/clear_dataset     Удалить датасет
/export_dataset    Экспортировать датасет
/thoughts_start    Запустить автосообщения
/thoughts_stop     Остановить автосообщения
/thoughts_add      Добавить тему для автосообщений
/thoughts_list     Показать все темы
/thoughts_time     Установить время отправки
/thoughts_now      Отправить сообщение сейчас
```

## Конфигурация

В .env файле:

```
BOT_TOKEN              Telegram bot token (обязательно)
BOT_USERNAME           Имя бота в Telegram
ADMIN_USER_ID          ID администратора
POLLINATIONS_MODEL     Модель AI: openai, mistral, llama (default: openai)
RATE_LIMIT_SECONDS     Задержка между ответами в секундах (default: 2)
PORT                   Порт для облака (default: 10000)
```

Доступные модели Pollinations:
- openai - GPT-4o-mini
- mistral - Mistral 7B
- llama - Llama 2
- deepseek - DeepSeek
- command-r-plus - Command R+

## Структура проекта

```
.
├── main.py                Основной код бота
├── requirements.txt       Python зависимости
├── .env.example          Шаблон переменных окружения
├── .env                  Ваша конфигурация (не коммитится)
├── check_setup.py        Скрипт проверки настройки
├── run.bat               Батник для быстрого запуска на Windows
│
├── dataset.txt           Датасет обучения (USER/ASSISTANT пары)
├── bot_stats.json        Статистика использования
├── blacklist.json        Чёрный список пользователей
├── user_consent.json     Согласия на обработку данных
└── bot_chats.json        История сообщений
```

## Как это работает

Процесс обработки сообщения:

1. Пользователь отправляет сообщение в Telegram
2. Бот проверяет триггеры (слово "азово", "@имя_бота" или другие)
3. Если триггер найден - сообщение добавляется в очередь
4. Очередь обрабатывает сообщения по очереди (rate limit 2 сек)
5. Отправляется запрос на AI (Pollinations.ai или Ollama)
6. AI возвращает ответ
7. Ответ отправляется в Telegram с реакцией
8. Сообщение сохраняется в датасет для истории

Триггеры (по умолчанию):
- "азово" - русский
- "azovo" - английский
- "@имя_бота" - упоминание бота

Это можно менять в main.py переменная TRIGGER_WORDS.

## Безопасность

- Чёрный список (blacklist.json) блокирует определённых пользователей
- Rate limiting (2 сек по умолчанию) защищает от спама
- BOT_TOKEN хранится в .env и НЕ коммитится в гит
- Все события логируются в консоль
- Логирование на уровне ERROR/WARNING/INFO

Как заблокировать пользователя:

```python
# Добавить ID в blacklist.json
{
    "7451061064": true,
    "123456789": true
}
```

## Статистика

Бот автоматически собирает в bot_stats.json:
- Количество обработанных сообщений
- Количество активных пользователей
- Время работы бота
- История по дням

Команда `/bot` выведет сводку:
```
Bot Statistics
Messages: 524
Commands: 89
Dataset: 342 entries, 171 pairs
Users: 23
Uptime: 3d 5h 12m
```

## Разработка

Проверить что всё настроено:
```bash
python check_setup.py
```

Это выведет статус всех компонентов и ошибки если они есть.

Запустить с выводом логов:
```bash
python main.py
```

Вывод будет типа:
```
2024-04-03 15:45:23 - __main__ - INFO - Bot started successfully
2024-04-03 15:45:24 - __main__ - INFO - Model: openai (Pollinations.ai)
2024-04-03 15:45:30 - __main__ - INFO - Message from user 123: привет
```

## Контакты

Telegram: [@azovoAIbot](https://t.me/azovoAIbot)

---

[![GitHub stars](https://img.shields.io/github/stars/твой-ник/azovo-ai-bot?style=plastic&logo=github&logoColor=white&color=yellow)](https://github.com/Sobka228/AzovoAi/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/твой-ник/azovo-ai-bot?style=plastic&logo=github&logoColor=white&color=blue)](https://github.com/Sobka228/AzovoAi/network)
[![GitHub watchers](https://img.shields.io/github/watchers/твой-ник/azovo-ai-bot?style=plastic&logo=github&logoColor=white&color=green)](https://github.com/Sobka228/AzovoAi/watchers)
[![GitHub issues](https://img.shields.io/github/issues/твой-ник/azovo-ai-bot?style=plastic&logo=github&logoColor=white&color=red)](https://github.com/Sobka228/AzovoAi/issues)
