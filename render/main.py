import os
import sys
import asyncio
import time
import random
import json
from collections import defaultdict
from typing import cast
import requests
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, ReactionTypeEmoji
from aiogram.enums import ChatAction
from aiogram.utils.keyboard import InlineKeyboardBuilder
import logging
import datetime
import warnings

# ======== НАСТРОЙКИ ========
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
warnings.filterwarnings("ignore")

# .env для локальной разработки (на Render переменные задаются в Dashboard)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден! Задайте переменную окружения BOT_TOKEN")

# ---- Pollinations.ai ----
POLLINATIONS_URL = "https://text.pollinations.ai/"
POLLINATIONS_MODEL = os.getenv("POLLINATIONS_MODEL", "openai")

DATASET_FILE = "dataset.txt"
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "7451061064"))
RATE_LIMIT_SECONDS = 2
BOT_USERNAME = os.getenv("BOT_USERNAME", "azovoAIbot")
PORT = int(os.getenv("PORT", "10000"))

# Файлы данных
STATS_FILE = "bot_stats.json"
CONSENT_FILE = "user_consent.json"
BLACKLIST_FILE = "blacklist.json"

TRIGGER_WORDS = ["азово", "azovo", f"@{BOT_USERNAME.lower()}"]
BOT_START_TIME = int(time.time())

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ======== РЕАКЦИИ ========
TELEGRAM_REACTIONS = [
    "👍", "👎", "❤️", "🔥", "🥰", "👏", "😁", "🤔",
    "🤯", "😱", "🎉", "🤩", "🥺", "🤡", "💩"
]

REACTION_KEYWORDS = [
    "поставь реакцию", "реакцию поставь", "поставь рандомную реакцию",
    "поставь любую реакцию", "поставь смайлик", "оцени", "прореагируй",
    "сделай реакцию", "реакцию", "поставь 👍", "поставь ❤️", "поставь 🔥",
    "поставь 🥚", "поставь 😱", "реакция"
]

REACTION_MAP = {
    "👍": "👍", "лайк": "👍", "нравится": "👍",
    "👎": "👎", "дизлайк": "👎", "не нравится": "👎",
    "❤️": "❤️", "сердце": "❤️", "любовь": "❤️",
    "🔥": "🔥", "огонь": "🔥", "огненно": "🔥",
    "🥰": "🥰", "обожаю": "🥰", "влюблен": "🥰",
    "👏": "👏", "аплодисменты": "👏", "браво": "👏",
    "😁": "😁", "улыбка": "😁", "смех": "😁",
    "🤔": "🤔", "хмм": "🤔", "задумался": "🤔",
    "🤯": "🤯", "взрыв мозга": "🤯", "офигеть": "🤯",
    "😱": "😱", "ужас": "😱", "страх": "😱",
    "🎉": "🎉", "праздник": "🎉", "ура": "🎉",
    "🤩": "🤩", "восторг": "🤩", "вау": "🤩",
    "🥺": "🥺", "умоляю": "🥺", "жалко": "🥺",
    "🤡": "🤡", "клоун": "🤡", "цирк": "🤡",
    "💩": "💩", "говно": "💩", "какаха": "💩",
    "🥚": "🥚", "яйцо": "🥚", "яйца": "🥚",
    "🔋": "🔋", "батарейка": "🔋", "крона": "🔋",
    "🐲": "🐲", "зверь": "🐲", "дракон": "🐲"
}

BOT_COMMANDS = [
    'reset', 'queue', 'start', 'bot', 'ping', 'save',
    'dataset_stats', 'clear_dataset', 'export_dataset',
    'thoughts_start', 'thoughts_stop', 'thoughts_add',
    'thoughts_remove', 'thoughts_time', 'thoughts_now', 'thoughts_list'
]

# ======== ЧЁРНЫЙ СПИСОК ========
DEFAULT_BLACKLIST = ["пах", "пax"]

def load_blacklist():
    if os.path.exists(BLACKLIST_FILE):
        try:
            with open(BLACKLIST_FILE, 'r', encoding='utf-8') as f:
                return json.load(f).get("words", [])
        except Exception:
            return DEFAULT_BLACKLIST.copy()
    save_blacklist(DEFAULT_BLACKLIST)
    return DEFAULT_BLACKLIST.copy()

def save_blacklist(words):
    with open(BLACKLIST_FILE, 'w', encoding='utf-8') as f:
        json.dump({"words": words}, f, ensure_ascii=False, indent=2)

def is_blacklisted(text):
    if not text:
        return False
    text_lower = text.lower()
    for word in load_blacklist():
        if word in text_lower:
            return True
    return False

# ======== СОГЛАСИЕ ========
def load_consent():
    if os.path.exists(CONSENT_FILE):
        try:
            with open(CONSENT_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_consent(data):
    with open(CONSENT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def has_user_consent(user_id):
    return str(user_id) in load_consent()

def set_user_consent(user_id):
    data = load_consent()
    data[str(user_id)] = {"consent_time": int(time.time()), "consent_version": "1.0"}
    save_consent(data)

# ======== СТАТИСТИКА ========
def get_default_stats():
    t = int(time.time())
    return {
        "total_messages": 0, "total_commands": 0, "total_thoughts": 0,
        "users": {}, "first_start": t, "last_restart": t
    }

def load_stats():
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if "users" in data and "total_messages" in data:
                    return data
        except Exception:
            pass
    return get_default_stats()

def save_stats(s):
    try:
        with open(STATS_FILE, 'w', encoding='utf-8') as f:
            json.dump(s, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Ошибка сохранения статистики: {e}")

stats = load_stats()

def update_stats(user_id, message_type="message"):
    global stats
    uid = str(user_id)
    stats["total_messages"] += 1
    if message_type == "command":
        stats["total_commands"] += 1
    elif message_type == "thought":
        stats["total_thoughts"] += 1
    if uid not in stats["users"]:
        stats["users"][uid] = {
            "first_seen": int(time.time()),
            "messages_count": 0,
            "commands_count": 0,
            "thoughts_count": 0
        }
    stats["users"][uid]["messages_count"] += 1
    if message_type == "command":
        stats["users"][uid]["commands_count"] += 1
    elif message_type == "thought":
        stats["users"][uid]["thoughts_count"] += 1
    save_stats(stats)

# ======== ОЧЕРЕДЬ ========
request_queue: asyncio.Queue = asyncio.Queue()
user_last_time: dict[int, float] = defaultdict(float)

def is_after_start(message: Message) -> bool:
    return int(message.date.timestamp()) >= BOT_START_TIME

# ======== РЕАКЦИИ ========
async def check_and_set_reaction(message: Message) -> bool:
    if not message.text:
        return False
    text_lower = message.text.lower().strip()
    if not any(kw in text_lower for kw in REACTION_KEYWORDS):
        return False
    reaction = None
    for word, emoji in REACTION_MAP.items():
        if word in text_lower:
            reaction = emoji
            break
    if not reaction:
        reaction = random.choice(TELEGRAM_REACTIONS)
    try:
        await message.react([ReactionTypeEmoji(emoji=reaction)])
        return True
    except Exception as e:
        logger.warning(f"Не удалось поставить реакцию: {e}")
        return False

async def notify_queue_position(message: Message, position: int):
    await message.answer(f"Ты в очереди, братан. Позиция: {position}. Жди, не дёргайся.")

def should_respond(message: Message) -> bool:
    if not message.chat or not message.from_user:
        return False
    if message.chat.type == "private" and not has_user_consent(message.from_user.id):
        return False
    if not is_after_start(message):
        return False
    if message.chat.type == "private":
        return True
    if not message.text:
        return False
    text_lower = message.text.lower()
    if f"@{BOT_USERNAME.lower()}" in text_lower:
        return True
    for word in TRIGGER_WORDS:
        if word in text_lower:
            return True
    if (message.reply_to_message
            and message.reply_to_message.from_user
            and message.reply_to_message.from_user.id == bot.id):
        return True
    return False

# ======== ДАТАСЕТ ========
def read_dataset():
    if not os.path.exists(DATASET_FILE):
        return []
    with open(DATASET_FILE, "r", encoding="utf-8") as f:
        return [l.strip() for l in f if l.strip()]

def append_to_dataset(text: str):
    with open(DATASET_FILE, "a", encoding="utf-8") as f:
        f.write(text.strip() + "\n")

def get_dataset_size():
    if not os.path.exists(DATASET_FILE):
        return 0
    with open(DATASET_FILE, "r", encoding="utf-8") as f:
        return sum(1 for _ in f)

def get_dataset_content():
    if not os.path.exists(DATASET_FILE):
        return "Датасет пуст"
    with open(DATASET_FILE, "r", encoding="utf-8") as f:
        return f.read()

def convert_to_train_format():
    lines = read_dataset()
    pairs = []
    i = 0
    while i < len(lines) - 1:
        if lines[i].startswith("USER:") and lines[i + 1].startswith("ASSISTANT:"):
            u = lines[i].replace("USER:", "").strip()
            a = lines[i + 1].replace("ASSISTANT:", "").strip()
            if u and a:
                pairs.append((u, a))
            i += 2
        else:
            i += 1
    return pairs

# промпт
SYSTEM_PROMPT = (
    "ты хам ебаный отвечай коротко и с маленькой буквы без знаков препинания "
    "матерись как сапожник если чел норм отвечай хамовато если чел хамит в ответ "
    "хами еще сильнее иногда сходи с ума пиши рандомные хуйни про яйца батарейки "
    "крону зверя в проводах пукизм и азovo если чел достал пошли нахуй если чел "
    "грубит ответь еще грубее никогда не извиняйся не будь вежливым вообще никаких "
    "знаков препинания только буквы и маты и с маленькой буквы"
)

def ask_ai(user_text: str) -> str:
    """Отправляет запрос к Pollinations.ai и возвращает ответ."""
    try:
        payload = {
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_text},
            ],
            "model": POLLINATIONS_MODEL,
            "seed": random.randint(1, 999999),
            "jsonMode": False,
        }

        resp = requests.post(
            POLLINATIONS_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=120,
        )

        if resp.status_code != 200:
            logger.error(f"Pollinations вернул {resp.status_code}: {resp.text[:300]}")
            return f"ошибка {resp.status_code} блять"

        text = resp.text.strip()

        try:
            data = json.loads(text)
            if isinstance(data, dict):
                choices = data.get("choices", [])
                if choices:
                    return (
                        choices[0]
                        .get("message", {})
                        .get("content", "нихуя не понял")
                        .strip()
                    )
                for key in ("text", "response", "content", "output"):
                    if key in data:
                        return str(data[key]).strip()
        except (json.JSONDecodeError, KeyError, IndexError):
            pass

        return text if text else "нихуя не понял"

    except requests.Timeout:
        return "таймаут блять попробуй позже"
    except requests.ConnectionError:
        return "нет связи с мозгами попробуй позже"
    except Exception as e:
        logger.exception("ask_ai error")
        return f"всё упало: {e}"

# ОБРАБОТЧИК ОЧЕРЕДИ
async def queue_processor():
    while True:
        msg, loop = await request_queue.get()
        try:
            await bot.send_chat_action(chat_id=msg.chat.id, action=ChatAction.TYPING)

            if msg.photo:
                reply = "Фото пока не умею обрабатывать, сорян! 📸"
                append_to_dataset(f"USER: [ФОТО] {msg.caption or ''}")
                append_to_dataset(f"ASSISTANT: {reply}")
                await msg.reply(reply)
                update_stats(msg.from_user.id, "message")
            else:
                if msg.text and msg.text.startswith(
                    tuple(f'/{cmd}' for cmd in BOT_COMMANDS)
                ):
                    request_queue.task_done()
                    continue

                if await check_and_set_reaction(msg):
                    request_queue.task_done()
                    continue

                reply = await loop.run_in_executor(None, ask_ai, msg.text)
                append_to_dataset(f"USER: {msg.text or ''}")
                append_to_dataset(f"ASSISTANT: {reply}")
                await msg.reply(reply)
                update_stats(msg.from_user.id, "message")

        except Exception as e:
            logger.exception("queue_processor error")
            try:
                await msg.reply(f"Ошибка, бля: {e}")
            except Exception:
                pass
        finally:
            request_queue.task_done()

# ЕЖЕДНЕВНЫЕ МЫСЛИ
class DailyThoughts:
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.is_running = False
        self.task = None
        self.target_chats: list[dict] = []
        self.hour = 12
        self.minute = 0

    def add_chat(self, chat_id: int, chat_title: str):
        for c in self.target_chats:
            if c["id"] == chat_id:
                return False, "Чат уже есть"
        self.target_chats.append({
            "id": chat_id, "title": chat_title, "added_at": time.time()
        })
        return True, f"Чат '{chat_title}' добавлен"

    def remove_chat(self, chat_id: int):
        for i, c in enumerate(self.target_chats):
            if c["id"] == chat_id:
                self.target_chats.pop(i)
                return True, f"Чат '{c['title']}' удалён"
        return False, "Чат не найден"

    def remove_chat_by_index(self, index: int):
        if 0 <= index < len(self.target_chats):
            c = self.target_chats.pop(index)
            return True, f"Чат '{c['title']}' удалён"
        return False, "Неверный индекс"

    def set_time(self, hour: int, minute: int):
        self.hour = hour
        self.minute = minute

    async def generate_thought(self):
        prompts = [
            "Напиши одну случайную мысль про яйца, батарейки или зверя",
            "Что ты думаешь о жизни? Ответь как шизофазик",
            "Сгенерируй случайную хуйню про яйца и провода",
            "Расскажи одну мысль про батарейки крона",
            "Что там у зверя в проводах? Напиши кратко",
        ]
        try:
            loop = asyncio.get_running_loop()
            thought = await loop.run_in_executor(
                None, ask_ai, random.choice(prompts)
            )
            return thought[:200] + ("..." if len(thought) > 200 else "")
        except Exception:
            return "яйцо батарейку грызёт 🤪"

    async def get_random_thoughts(self, mn=3, mx=7):
        count = random.randint(mn, mx)
        result = []
        for i in range(count):
            t = await self.generate_thought()
            result.append(f"{i + 1}. {t}")
            await asyncio.sleep(1)
        return result

    async def send_daily_thoughts(self):
        if not self.target_chats:
            return
        thoughts = await self.get_random_thoughts()
        message_text = "🧠 **ЕЖЕДНЕВНЫЕ МЫСЛИ** 🧠\n\n" + "\n".join(thoughts)
        for chat in self.target_chats:
            try:
                await self.bot.send_message(
                    chat_id=chat["id"], text=message_text, parse_mode="Markdown"
                )
                update_stats(ADMIN_USER_ID, "thought")
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Ошибка отправки мыслей в {chat['title']}: {e}")

    async def daily_loop(self):
        while self.is_running:
            now = datetime.datetime.now()
            target = now.replace(
                hour=self.hour, minute=self.minute, second=0, microsecond=0
            )
            if now > target:
                target += datetime.timedelta(days=1)
            await asyncio.sleep((target - now).total_seconds())
            if self.is_running:
                await self.send_daily_thoughts()

    def start(self):
        if not self.is_running:
            self.is_running = True
            self.task = asyncio.create_task(self.daily_loop())

    def stop(self):
        self.is_running = False
        if self.task:
            self.task.cancel()

    def get_chats_list(self):
        return self.target_chats

daily_thoughts = DailyThoughts(bot)

# КОМАНДЫ
@dp.message(Command("save"))
async def cmd_save(message: Message):
    if not message.from_user or message.from_user.id != ADMIN_USER_ID:
        return await message.reply("❌ Только для админа!")
    sz = get_dataset_size()
    await message.reply(
        f"💾 **ДАТАСЕТ СОХРАНЁН**\n\n"
        f"📊 Строк: {sz}\n📁 Файл: `{DATASET_FILE}`",
        parse_mode="Markdown",
    )
    update_stats(message.from_user.id, "command")

@dp.message(Command("ping"))
async def cmd_ping(message: Message):
    t0 = time.time()
    msg = await message.reply("🏓 **Понг...**")
    ping_ms = round((time.time() - t0) * 1000, 2)
    uptime = str(datetime.timedelta(seconds=int(time.time() - stats["last_restart"])))
    await msg.edit_text(
        f"🏓 **ПОНГ!**\n\n"
        f"📡 Задержка: `{ping_ms} мс`\n"
        f"⏱️ Аптайм: `{uptime}`\n"
        f"🤖 Модель: `{POLLINATIONS_MODEL}` (Pollinations.ai)\n\n"
        f"🥚 Яйцо куриное!",
        parse_mode="Markdown",
    )
    if message.from_user:
        update_stats(message.from_user.id, "command")

@dp.message(Command("reset"))
async def reset_chat(message: Message):
    if not message.from_user or message.from_user.id != ADMIN_USER_ID:
        return await message.reply("Ты не админ, иди батарейки лижи! 🔋")
    await message.reply("🧹 Память очищена, бля! Теперь как новенький!")
    update_stats(message.from_user.id, "command")

@dp.message(Command("bot"))
async def bot_stats(message: Message):
    if not message.from_user or not message.chat:
        return
    if not has_user_consent(message.from_user.id) and message.chat.type == "private":
        return await show_policy(message)
    up = int(time.time()) - stats["last_restart"]
    d, rem = divmod(up, 86400)
    h, rem = divmod(rem, 3600)
    m, _ = divmod(rem, 60)
    ds = get_dataset_size()
    pairs = convert_to_train_format()
    await message.reply(
        f"🤖 **СТАТИСТИКА БОТА**\n\n"
        f"📊 Сообщений: {stats['total_messages']}\n"
        f"⚙️ Команд: {stats['total_commands']}\n"
        f"💭 Мыслей: {stats['total_thoughts']}\n"
        f"📚 Датасет: {ds} строк, {len(pairs)} пар\n"
        f"👥 Пользователей: {len(stats['users'])}\n"
        f"⏱️ Аптайм: {d}д {h}ч {m}м\n"
        f"🤖 Модель: `{POLLINATIONS_MODEL}` (Pollinations.ai)",
        parse_mode="Markdown",
    )
    update_stats(message.from_user.id, "command")

@dp.message(Command("dataset_stats"))
async def cmd_dataset_stats(message: Message):
    if not message.from_user or message.from_user.id != ADMIN_USER_ID:
        return await message.reply("❌ Только для админа!")
    ds = get_dataset_size()
    pairs = convert_to_train_format()
    await message.reply(
        f"📊 **ДАТАСЕТ**\n📄 Строк: {ds}\n💬 Пар: {len(pairs)}\n📁 `{DATASET_FILE}`",
        parse_mode="Markdown",
    )
    update_stats(message.from_user.id, "command")

@dp.message(Command("clear_dataset"))
async def cmd_clear_dataset(message: Message):
    if not message.from_user or message.from_user.id != ADMIN_USER_ID:
        return await message.reply("❌ Только для админа!")
    with open(DATASET_FILE, "w", encoding="utf-8") as f:
        f.write("")
    await message.reply("🗑️ **ДАТАСЕТ ОЧИЩЕН**", parse_mode="Markdown")
    update_stats(message.from_user.id, "command")

@dp.message(Command("export_dataset"))
async def cmd_export_dataset(message: Message):
    if not message.from_user or message.from_user.id != ADMIN_USER_ID:
        return await message.reply("❌ Только для админа!")
    content = get_dataset_content()
    ds = get_dataset_size()
    pairs = convert_to_train_format()
    if len(content) > 4000:
        tmp = f"dataset_export_{int(time.time())}.txt"
        with open(tmp, "w", encoding="utf-8") as f:
            f.write(content)
        await message.reply_document(
            types.FSInputFile(tmp),
            caption=f"📁 Датасет\n📊 Строк: {ds}\n💬 Пар: {len(pairs)}",
        )
        os.remove(tmp)
    else:
        await message.reply(
            f"📁 **ДАТАСЕТ**\n📊 Строк: {ds}\n💬 Пар: {len(pairs)}\n\n```\n{content}\n```",
            parse_mode="Markdown",
        )
    update_stats(message.from_user.id, "command")

# мысли
@dp.message(Command("thoughts_start"))
async def cmd_thoughts_start(message: Message):
    if not message.from_user or message.from_user.id != ADMIN_USER_ID:
        return await message.reply("❌ Только для админа!")
    daily_thoughts.start()
    await message.reply(
        f"✅ Мысли запущены\n🕐 Время: {daily_thoughts.hour:02d}:{daily_thoughts.minute:02d}"
    )
    update_stats(message.from_user.id, "command")

@dp.message(Command("thoughts_stop"))
async def cmd_thoughts_stop(message: Message):
    if not message.from_user or message.from_user.id != ADMIN_USER_ID:
        return await message.reply("❌ Только для админа!")
    daily_thoughts.stop()
    await message.reply("🛑 Мысли остановлены")
    update_stats(message.from_user.id, "command")

@dp.message(Command("thoughts_add"))
async def cmd_thoughts_add(message: Message):
    if not message.from_user or message.from_user.id != ADMIN_USER_ID:
        return await message.reply("❌ Только для админа!")
    if not message.text:
        return await message.reply("❌ Укажите ссылку на чат")
    args = message.text.split(maxsplit=1)
    if len(args) > 1:
        link = args[1].strip()
        try:
            if link.startswith("https://t.me/"):
                chat_username = "@" + link.replace("https://t.me/", "").split("/")[0]
            elif link.startswith("@"):
                chat_username = link
            else:
                return await message.reply("❌ Неверный формат")
            chat = await bot.get_chat(chat_username)
            if chat and hasattr(chat, "id"):
                title = chat.title or chat.username or f"Чат {chat.id}"
                ok, msg_text = daily_thoughts.add_chat(chat.id, title)
                await message.reply(f"{'✅' if ok else '⚠️'} {msg_text}")
            else:
                await message.reply("❌ Не удалось получить инфо о чате")
        except Exception as e:
            await message.reply(f"❌ Ошибка: {e}")
    else:
        if message.chat:
            title = message.chat.title or message.chat.username or f"Чат {message.chat.id}"
            ok, msg_text = daily_thoughts.add_chat(message.chat.id, title)
            await message.reply(f"{'✅' if ok else '⚠️'} {msg_text}")
    update_stats(message.from_user.id, "command")

@dp.message(Command("thoughts_remove"))
async def cmd_thoughts_remove(message: Message):
    if not message.from_user or message.from_user.id != ADMIN_USER_ID:
        return await message.reply("❌ Только для админа!")
    if message.chat:
        ok, msg_text = daily_thoughts.remove_chat(message.chat.id)
        await message.reply(f"{'✅' if ok else '⚠️'} {msg_text}")
    update_stats(message.from_user.id, "command")

@dp.message(Command("thoughts_time"))
async def cmd_thoughts_time(message: Message):
    if not message.from_user or message.from_user.id != ADMIN_USER_ID:
        return await message.reply("❌ Только для админа!")
    if not message.text:
        return await message.reply("❌ /thoughts_time ЧЧ ММ")
    args = message.text.split()
    if len(args) < 3:
        return await message.reply("❌ /thoughts_time ЧЧ ММ")
    try:
        daily_thoughts.set_time(int(args[1]), int(args[2]))
        await message.reply(f"✅ Время: {int(args[1]):02d}:{int(args[2]):02d}")
    except Exception:
        await message.reply("❌ Неверный формат")
    update_stats(message.from_user.id, "command")

@dp.message(Command("thoughts_now"))
async def cmd_thoughts_now(message: Message):
    if not message.from_user or message.from_user.id != ADMIN_USER_ID:
        return await message.reply("❌ Только для админа!")
    await message.reply("🧠 Генерирую мысли...")
    thoughts = await daily_thoughts.get_random_thoughts(5, 10)
    await message.reply("\n".join(thoughts))
    update_stats(message.from_user.id, "command")

@dp.message(Command("thoughts_list"))
async def cmd_thoughts_list(message: Message):
    if not message.from_user or message.from_user.id != ADMIN_USER_ID:
        return await message.reply("❌ Только для админа!")
    chats = daily_thoughts.get_chats_list()
    if chats:
        text = "📋 **ЧАТЫ:**\n\n"
        for i, c in enumerate(chats, 1):
            text += f"{i}. {c['title']} (`{c['id']}`)\n"
        await message.reply(text, parse_mode="Markdown")
    else:
        await message.reply("📭 Список пуст")
    update_stats(message.from_user.id, "command")

# ======== ПОЛИТИКА ========
async def show_policy(message: Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Я согласен", callback_data="accept_policy")
    builder.button(
        text="📄 Подробнее",
        url="https://telegra.ph/Politika-bota-AzovoAI-03-06",
    )
    await message.answer(
        "📜 **ПОЛИТИКА БОТА**\n\nНажимая «Я согласен», вы подтверждаете согласие.",
        reply_markup=builder.as_markup(),
        parse_mode="Markdown",
    )

@dp.callback_query(F.data == "accept_policy")
async def accept_policy(callback: CallbackQuery):
    if callback.from_user:
        set_user_consent(callback.from_user.id)
    if callback.message is not None:
        msg = cast(Message, callback.message)
        await msg.edit_text(
            "✅ Доступ открыт!\n\n/bot — статистика\n/ping — задержка\n\nПросто пиши!"
        )
    await callback.answer()

# ======== СТАРТ ========
@dp.message(CommandStart())
async def start(message: Message):
    if not message.from_user or not message.chat:
        return
    if not has_user_consent(message.from_user.id):
        return await show_policy(message)
    builder = InlineKeyboardBuilder()
    bot_un = BOT_USERNAME.lstrip("@")
    builder.button(text="➕ Добавить в чат", url=f"https://t.me/{bot_un}?startgroup=true")
    await message.answer(
        "привет я новая нейросеть по имени азovoAI\n"
        "если че мое имя не связана с политикой или селом в Омской областе\n"
        "мой тгк - https://t.me/azovo_AI\n"
        "тгк моего владельца - https://t.me/SOBKA_TV\n"
        "добавь меня в свой чат",
        reply_markup=builder.as_markup(),
    )
    update_stats(message.from_user.id, "command")

@dp.message(Command("queue"))
async def queue_status(message: Message):
    if not message.from_user:
        return await message.reply("❌ Не удалось определить пользователя")
    if not has_user_consent(message.from_user.id) and message.chat and message.chat.type == "private":
        return await show_policy(message)
    pos = None
    try:
        for i in range(request_queue.qsize()):
            queued_msg, _ = request_queue._queue[i]
            if queued_msg.from_user and queued_msg.from_user.id == message.from_user.id:
                pos = i + 1
                break
    except Exception:
        pass
    await message.answer(f"Позиция: {pos}" if pos else "Тебя нет в очереди")
    update_stats(message.from_user.id, "command")

# ======== ОСНОВНОЙ ОБРАБОТЧИК ========
@dp.message()
async def handle_message(message: Message):
    if not message.from_user or not message.chat:
        return
    if message.text and message.text.startswith(tuple(f"/{c}" for c in BOT_COMMANDS)):
        return
    if not message.text:
        return
    if not should_respond(message):
        return
    if is_blacklisted(message.text):
        return

    uid = message.from_user.id
    now = time.time()
    if now - user_last_time[uid] < RATE_LIMIT_SECONDS:
        return await message.reply("не флуди")
    user_last_time[uid] = now

    loop = asyncio.get_running_loop()
    qsize = request_queue.qsize()
    await request_queue.put((message, loop))
    if qsize > 0:
        await notify_queue_position(message, qsize + 1)

# health-check
async def handle_health(request):
    uptime = int(time.time() - stats["last_restart"])
    return web.json_response({
        "status": "ok",
        "uptime": uptime,
        "model": POLLINATIONS_MODEL,
        "messages": stats["total_messages"],
        "users": len(stats["users"]),
    })

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_health)
    app.router.add_get("/health", handle_health)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    logger.info(f"Health-check сервер запущен на 0.0.0.0:{PORT}")
#   ЗАПУСК
async def on_startup():
    asyncio.create_task(queue_processor())
    global stats
    stats["last_restart"] = int(time.time())
    save_stats(stats)
    logger.info("✅ Бот запущен!")
    logger.info(f"🤖 Модель: {POLLINATIONS_MODEL} (Pollinations.ai)")
    logger.info(f"📁 Датасет: {DATASET_FILE}")

async def main():
    await start_web_server()
    dp.startup.register(on_startup)
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен")
