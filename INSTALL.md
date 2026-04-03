# Установка и запуск

## Требования

- **Python 3.8+**
- **pip**
- **Интернет**
- **Telegram bot token** (получите от [@BotFather](https://t.me/BotFather))
- **ВПН** (если вы находитесь в РФ)
 ## Шаг 1: Получите токен

1. Откройте Telegram и напишите [@BotFather](https://t.me/BotFather)
2. Команда: `/newbot`
3. Придумайте имя и юзернейм
4. Скопируйте токен

## Шаг 2: Клонируйте репо

```bash
git clone https://github.com/Sobka228/azovoai.git
cd azovoai
```
Или скачайте ZIP и распакуйте.

## Шаг 3: Создайте .env

```bash
cp .env.example .env
```

Отредактируйте `.env`:

```env
BOT_TOKEN=ВАШ_ТОКЕН_СЮДА
BOT_USERNAME=azovoAIbot
ADMIN_USER_ID=7451061064
POLLINATIONS_MODEL=openai
RATE_LIMIT_SECONDS=2
PORT=10000
```

**Обязательно**: `BOT_TOKEN` должен быть заполнен

## Шаг 4: Установите зависимости

```bash
pip install -r requirements.txt
```

Установятся:
- `aiogram==3.4.1` — Telegram API
- `requests==2.31.0` — HTTP requests
- `python-dotenv==1.0.0` — .env файлы

## Шаг 5: Запустите бота

### Windows

```bash
run.bat
```

Или вручную:
```bash
python main.py
```

### Linux/Mac

```bash
python main.py
```

или

```bash
python3 main.py
```

```bash
# Проверить настройку
python check_setup.py

# Установить актуальные версии пакетов
pip install -r requirements.txt --upgrade

# Видеть версии установленных пакетов
pip list

# Удалить все зависимости
pip uninstall -r requirements.txt -y
```

## Структура папок

```
.
├── main.py                # Основной скрипт
├── requirements.txt       # Зависимости pip
├── .env                   # Ваша конфигурация (не коммитится в git)
├── .env.example          # Шаблон для .env
├── check_setup.py        # Скрипт проверки
├── run.bat               # Батник для Windows
│
├── dataset.txt           # Датасет сообщений
├── bot_stats.json        # Статистика бота
├── blacklist.json        # Заблокированные пользователи
├── user_consent.json     # Согласия пользователей
└── bot_chats.json        # История сообщений
```

## Первый запуск создаст

При первом запуске бот создаст файлы автоматически:

- `bot_stats.json` — Статистика использования
- `user_consent.json` — Кто дал согласие
- `blacklist.json` — Чёрный список

Файл `dataset.txt` уже есть с примерами.

## Готово

Ваш бот запущен и работает.

Дальше:
- Смотрите [COMMANDS.md](COMMANDS.md) для всех команд
- [CUSTOMIZE.md](CUSTOMIZE.md) для кастомизации
- [DEPLOY.md](DEPLOY.md) для развёртывания на облаке

---
