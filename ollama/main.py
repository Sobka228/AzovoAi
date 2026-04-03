
import os
import sys
import asyncio
import time
import random
import json
from collections import defaultdict
from typing import cast
import requests
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, ReactionTypeEmoji
from aiogram.enums import ChatAction
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv
import logging
import datetime
import warnings

# Настраиваем логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Подавляем предупреждения
warnings.filterwarnings("ignore")

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN") or ""
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в переменных окружения")
# ТОЛЬКО БАЗОВАЯ МОДЕЛЬ - VIKHR LLAMA
MODEL_NAME = "hf.co/itlwas/Vikhr-Llama-3.2-1B-Instruct-abliterated-Q4_K_M-GGUF:latest"
DATASET_FILE = "dataset.txt"
ADMIN_USER_ID = 7451061064
RATE_LIMIT_SECONDS = 2
BOT_USERNAME = os.getenv("BOT_USERNAME", "azovoAIbot")

# Файлы
STATS_FILE = "bot_stats.json"
CONSENT_FILE = "user_consent.json"
BLACKLIST_FILE = "blacklist.json"

TRIGGER_WORDS = ["азово", "azovo", f"@{BOT_USERNAME.lower()}"]
BOT_START_TIME = int(time.time())

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# ======== СТАНДАРТНЫЕ РЕАКЦИИ ========
TELEGRAM_REACTIONS = ["👍", "👎", "❤️", "🔥", "🥰", "👏", "😁", "🤔", "🤯", "😱", "🎉", "🤩", "🥺", "🤡", "💩"]

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

BOT_COMMANDS = ['reset', 'queue', 'start', 'bot', 'ping', 'save', 'dataset_stats', 'clear_dataset', 'export_dataset', 'thoughts_start', 'thoughts_stop', 'thoughts_add', 'thoughts_remove', 'thoughts_time', 'thoughts_now', 'thoughts_list']

# ======== ЧЁРНЫЙ СПИСОК ========
DEFAULT_BLACKLIST = ["пах", "пax"]

def load_blacklist():
    if os.path.exists(BLACKLIST_FILE):
        try:
            with open(BLACKLIST_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("words", [])
        except:
            return DEFAULT_BLACKLIST.copy()
    else:
        save_blacklist(DEFAULT_BLACKLIST)
        return DEFAULT_BLACKLIST.copy()

def save_blacklist(words):
    with open(BLACKLIST_FILE, 'w', encoding='utf-8') as f:
        json.dump({"words": words}, f, ensure_ascii=False, indent=2)

def is_blacklisted(text):
    if not text:
        return False
    text_lower = text.lower()
    words = load_blacklist()
    for word in words:
        if word in text_lower:
            return True
    return False

# ======== СИСТЕМА СОГЛАСИЯ ========
def load_consent():
    if os.path.exists(CONSENT_FILE):
        try:
            with open(CONSENT_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_consent(consent_data):
    with open(CONSENT_FILE, 'w', encoding='utf-8') as f:
        json.dump(consent_data, f, ensure_ascii=False, indent=2)

def has_user_consent(user_id):
    consent_data = load_consent()
    return str(user_id) in consent_data

def set_user_consent(user_id):
    consent_data = load_consent()
    consent_data[str(user_id)] = {
        "consent_time": int(time.time()),
        "consent_version": "1.0"
    }
    save_consent(consent_data)

# ======== СТАТИСТИКА ========
def load_stats():
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if "users" in data and "total_messages" in data:
                    return data
        except:
            pass
    return get_default_stats()

def save_stats(stats_data):
    try:
        with open(STATS_FILE, 'w', encoding='utf-8') as f:
            json.dump(stats_data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Ошибка сохранения статистики: {e}")
        return False

def get_default_stats():
    current_time = int(time.time())
    return {
        "total_messages": 0,
        "total_commands": 0,
        "total_thoughts": 0,
        "users": {},
        "first_start": current_time,
        "last_restart": current_time
    }

stats = load_stats()

def update_stats(user_id, message_type="message"):
    global stats
    user_id = str(user_id)
    stats["total_messages"] += 1
    if message_type == "command":
        stats["total_commands"] += 1
    elif message_type == "thought":
        stats["total_thoughts"] += 1
    if user_id not in stats["users"]:
        stats["users"][user_id] = {
            "first_seen": int(time.time()),
            "messages_count": 0,
            "commands_count": 0,
            "thoughts_count": 0
        }
    stats["users"][user_id]["messages_count"] += 1
    if message_type == "command":
        stats["users"][user_id]["commands_count"] += 1
    elif message_type == "thought":
        stats["users"][user_id]["thoughts_count"] += 1
    save_stats(stats)

# ======== ОЧЕРЕДЬ ========
request_queue = asyncio.Queue()
user_last_time = defaultdict(float)

def is_after_start(message: Message) -> bool:
    message_time = int(message.date.timestamp())
    return message_time >= BOT_START_TIME

# ======== ФУНКЦИЯ ДЛЯ РЕАКЦИЙ ========
async def check_and_set_reaction(message: Message) -> bool:
    if not message.text:
        return False
    
    text_lower = message.text.lower().strip()
    is_reaction_request = any(keyword in text_lower for keyword in REACTION_KEYWORDS)
    
    if not is_reaction_request:
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
        print(f"Не удалось поставить реакцию: {e}")
        return False

async def notify_queue_position(message: Message, position: int):
    await message.answer(f"Ты в очереди, братан. Позиция: {position}. Жди, не дёргайся.")

# ======== ФИЛЬТРЫ И ДАТАСЕТ ========
def is_safe_text(text: str) -> bool:
    if not text:
        return True
    text_lower = text.lower()
    banned_words = ["cp", "child porn", "детское порно"]
    return not any(word in text_lower for word in banned_words)

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
    if message.reply_to_message and message.reply_to_message.from_user and message.reply_to_message.from_user.id == bot.id:
        return True
    return False

# ======== ДАТАСЕТ ========
def read_dataset():
    if not os.path.exists(DATASET_FILE):
        return []
    with open(DATASET_FILE, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
    return lines

def append_to_dataset(text: str):
    if is_safe_text(text):
        with open(DATASET_FILE, "a", encoding="utf-8") as f:
            f.write(text.strip() + "\n")

def get_dataset_size():
    if not os.path.exists(DATASET_FILE):
        return 0
    with open(DATASET_FILE, "r", encoding="utf-8") as f:
        return len(f.readlines())

def get_dataset_content():
    """Возвращает полное содержимое датасета"""
    if not os.path.exists(DATASET_FILE):
        return "Датасет пуст"
    with open(DATASET_FILE, "r", encoding="utf-8") as f:
        return f.read()

def convert_to_train_format():
    lines = read_dataset()
    pairs = []
    i = 0
    while i < len(lines) - 1:
        if lines[i].startswith("USER:") and lines[i+1].startswith("ASSISTANT:"):
            user_text = lines[i].replace("USER:", "").strip()
            assistant_text = lines[i+1].replace("ASSISTANT:", "").strip()
            if user_text and assistant_text:
                pairs.append((user_text, assistant_text))
            i += 2
        else:
            i += 1
    return pairs

# ======== OLLAMA ========
def ask_ollama(user_text):
    """Использует базовую модель для ответа"""
    try:
        # Системный промпт
        system_prompt = """ты хам ебаный отвечай коротко и с маленькой буквы без знаков препинания матерись как сапожник если чел норм отвечай хамовато если чел хамит в ответ хами еще сильнее иногда сходи с ума пиши рандомные хуйни про яйца батарейки крону зверя в проводах пукизм и азovo если чел достал пошли нахуй если чел грубит ответь еще грубее никогда не извиняйся не будь вежливым вообще никаких знаков препинания только буквы и маты и с маленькой буквы"""
        
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": MODEL_NAME,
                "prompt": user_text,
                "system": system_prompt,
                "stream": False,
                "options": {
                    "temperature": 1.3,
                    "num_predict": 100,
                    "top_p": 0.9
                }
            },
            timeout=30
        )
        if response.status_code != 200:
            return f"Ошибка {response.status_code}"
        result = response.json()
        reply = result.get("response", "Нихуя не понял").strip()
        return reply
    except Exception as e:
        return f"Всё упало: {str(e)}"

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
                if msg.text and msg.text.startswith(tuple(f'/{cmd}' for cmd in BOT_COMMANDS)):
                    continue
                
                reaction_result = await check_and_set_reaction(msg)
                if reaction_result:
                    continue
                
                reply = await loop.run_in_executor(None, ask_ollama, msg.text)
                append_to_dataset(f"USER: {msg.text or ''}")
                append_to_dataset(f"ASSISTANT: {reply}")
                await msg.reply(reply)
                update_stats(msg.from_user.id, "message")
                    
        except Exception as e:
            await msg.reply(f"Ошибка, бля: {e}")
        finally:
            request_queue.task_done()

# ======== ЕЖЕДНЕВНЫЕ МЫСЛИ ========
class DailyThoughts:
    def __init__(self, bot_instance):
        self.bot = bot_instance
        self.is_running = False
        self.task = None
        self.target_chats = []
        self.hour = 12
        self.minute = 0
    
    def add_chat(self, chat_id: int, chat_title: str) -> tuple[bool, str]:
        for chat in self.target_chats:
            if chat["id"] == chat_id:
                return False, "Чат уже есть в списке"
        self.target_chats.append({
            "id": chat_id,
            "title": chat_title,
            "added_at": time.time()
        })
        return True, f"Чат '{chat_title}' добавлен"
    
    def remove_chat(self, chat_id: int) -> tuple[bool, str]:
        for i, chat in enumerate(self.target_chats):
            if chat["id"] == chat_id:
                self.target_chats.pop(i)
                return True, f"Чат '{chat['title']}' удален"
        return False, "Чат не найден"
    
    def remove_chat_by_index(self, index: int) -> tuple[bool, str]:
        if 0 <= index < len(self.target_chats):
            chat = self.target_chats.pop(index)
            return True, f"Чат '{chat['title']}' удален"
        return False, "Неверный индекс"
    
    def set_time(self, hour: int, minute: int) -> None:
        self.hour = hour
        self.minute = minute
    
    async def generate_thought(self):
        prompts = [
            "Напиши одну случайную мысль про яйца, батарейки или зверя",
            "Что ты думаешь о жизни? Ответь как шизофазик",
            "Сгенерируй случайную хуйню про яйца и провода",
            "Расскажи одну мысль про батарейки крона",
            "Что там у зверя в проводах? Напиши кратко"
        ]
        prompt = random.choice(prompts)
        try:
            loop = asyncio.get_running_loop()
            thought = await loop.run_in_executor(None, ask_ollama, prompt)
            if len(thought) > 200:
                thought = thought[:200] + "..."
            return thought
        except:
            return "яйцо батарейку грызёт 🤪"
    
    async def get_random_thoughts(self, min_count=3, max_count=7):
        count = random.randint(min_count, max_count)
        result = []
        for i in range(count):
            thought = await self.generate_thought()
            result.append(f"{i+1}. {thought}")
            await asyncio.sleep(1)
        return result
    
    async def send_daily_thoughts(self):
        if not self.target_chats:
            return
        
        thoughts = await self.get_random_thoughts()
        message = "🧠 **ЕЖЕДНЕВНЫЕ МЫСЛИ** 🧠\n\n" + "\n".join(thoughts)
        
        for chat in self.target_chats:
            try:
                await self.bot.send_message(chat_id=chat["id"], text=message, parse_mode="Markdown")
                update_stats(ADMIN_USER_ID, "thought")
                await asyncio.sleep(1)
            except Exception as e:
                print(f"❌ Ошибка отправки: {e}")
    
    async def daily_loop(self):
        while self.is_running:
            now = datetime.datetime.now()
            target_time = now.replace(hour=self.hour, minute=self.minute, second=0, microsecond=0)
            if now > target_time:
                target_time = target_time.replace(day=target_time.day + 1)
            wait_seconds = (target_time - now).total_seconds()
            await asyncio.sleep(wait_seconds)
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

# ======== АДМИНСКИЕ КОМАНДЫ ========

@dp.message(Command("save"))
async def cmd_save(message: Message):
    """Сохраняет датасет"""
    if not message.from_user or message.from_user.id != ADMIN_USER_ID:
        await message.reply("❌ Только для админа!")
        return
    
    dataset_lines = read_dataset()
    current_size = len(dataset_lines)
    
    await message.reply(
        f"💾 **ДАТАСЕТ СОХРАНЕН**\n\n"
        f"📊 **Текущий размер:** {current_size} строк\n"
        f"📁 **Файл:** `{DATASET_FILE}`"
    )
    update_stats(message.from_user.id, "command")
    append_to_dataset(f"ADMIN: Проверил датасет ({current_size} строк)")

@dp.message(Command("ping"))
async def cmd_ping(message: Message):
    start_time = time.time()
    msg = await message.reply("🏓 **Понг...**")
    end_time = time.time()
    ping_ms = round((end_time - start_time) * 1000, 2)
    uptime_seconds = int(time.time() - stats["last_restart"])
    uptime_str = str(datetime.timedelta(seconds=uptime_seconds))
    await msg.edit_text(
        f"🏓 **ПОНГ!**\n\n"
        f"📡 **Задержка:** `{ping_ms} мс`\n"
        f"⏱️ **Аптайм:** `{uptime_str}`\n"
        f"🤖 **Модель:** `{MODEL_NAME}`\n\n"
        f"🥚 **Яйцо куриное!**"
    )
    if message.from_user:
        update_stats(message.from_user.id, "command")

@dp.message(Command("reset"))
async def reset_chat(message: Message):
    if not message.from_user or message.from_user.id != ADMIN_USER_ID:
        await message.reply("Ты не админ, иди батарейки лижи! 🔋")
        return
    await message.reply("🧹 Память очищена, бля! Теперь я как новенький, даже яйца свежие!")
    append_to_dataset("ADMIN: Сбросил память чата")
    if message.from_user:
        update_stats(message.from_user.id, "command")

@dp.message(Command("bot"))
async def bot_stats(message: Message):
    if not message.from_user or not message.chat:
        return
    if not has_user_consent(message.from_user.id) and message.chat.type == "private":
        await show_policy(message)
        return
    
    current_time = int(time.time())
    uptime = current_time - stats["last_restart"]
    uptime_days = uptime // 86400
    uptime_hours = (uptime % 86400) // 3600
    uptime_minutes = (uptime % 3600) // 60
    
    dataset_size = get_dataset_size()
    pairs = convert_to_train_format()
    unique_users = len(stats["users"])
    
    text = (
        f"🤖 **СТАТИСТИКА БОТА**\n\n"
        f"📊 **Сообщений:** {stats['total_messages']}\n"
        f"⚙️ **Команд:** {stats['total_commands']}\n"
        f"💭 **Мыслей:** {stats['total_thoughts']}\n"
        f"📚 **Датасет:** {dataset_size} строк, {len(pairs)} пар\n"
        f"👥 **Пользователей:** {unique_users}\n"
        f"⏱️ **Аптайм:** {uptime_days}д {uptime_hours}ч {uptime_minutes}м\n"
        f"🤖 **Модель:** `{MODEL_NAME}`"
    )
    await message.reply(text, parse_mode="Markdown")
    if message.from_user:
        update_stats(message.from_user.id, "command")

@dp.message(Command("dataset_stats"))
async def cmd_dataset_stats(message: Message):
    """Статистика датасета"""
    if not message.from_user or message.from_user.id != ADMIN_USER_ID:
        await message.reply("❌ Только для админа!")
        return
    
    dataset_size = get_dataset_size()
    pairs = convert_to_train_format()
    
    text = (
        f"📊 **СТАТИСТИКА ДАТАСЕТА**\n\n"
        f"📄 **Строк:** {dataset_size}\n"
        f"💬 **Пар:** {len(pairs)}\n"
        f"📁 **Файл:** `{DATASET_FILE}`"
    )
    await message.reply(text, parse_mode="Markdown")
    if message.from_user:
        update_stats(message.from_user.id, "command")

@dp.message(Command("clear_dataset"))
async def cmd_clear_dataset(message: Message):
    """Очищает датасет"""
    if not message.from_user or message.from_user.id != ADMIN_USER_ID:
        await message.reply("❌ Только для админа!")
        return
    
    with open(DATASET_FILE, "w", encoding="utf-8") as f:
        f.write("")
    
    await message.reply("🗑️ **ДАТАСЕТ ОЧИЩЕН**")
    if message.from_user:
        update_stats(message.from_user.id, "command")

@dp.message(Command("export_dataset"))
async def cmd_export_dataset(message: Message):
    """Выгружает датасет"""
    if not message.from_user or message.from_user.id != ADMIN_USER_ID:
        await message.reply("❌ Только для админа!")
        return
    
    dataset_content = get_dataset_content()
    dataset_size = get_dataset_size()
    pairs = convert_to_train_format()
    
    if len(dataset_content) > 4000:
        # Если датасет большой, отправляем файлом
        temp_file = f"dataset_export_{int(time.time())}.txt"
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(dataset_content)
        
        with open(temp_file, "rb") as f:
            await message.reply_document(
                types.FSInputFile(temp_file),
                caption=f"📁 Датасет\n📊 Строк: {dataset_size}\n💬 Пар: {len(pairs)}"
            )
        os.remove(temp_file)
    else:
        await message.reply(
            f"📁 **СОДЕРЖИМОЕ ДАТАСЕТА**\n\n"
            f"📊 Строк: {dataset_size}\n"
            f"💬 Пар: {len(pairs)}\n\n"
            f"```\n{dataset_content}\n```"
        )
    
    update_stats(message.from_user.id, "command")

# ======== КОМАНДЫ ДЛЯ МЫСЛЕЙ ========

@dp.message(Command("thoughts_start"))
async def cmd_thoughts_start(message: Message):
    if not message.from_user or message.from_user.id != ADMIN_USER_ID:
        await message.reply("❌ Только для админа!")
        return
    daily_thoughts.start()
    await message.reply(f"✅ **Мысли запущены**\n🕐 Время: {daily_thoughts.hour:02d}:{daily_thoughts.minute:02d}")
    if message.from_user:
        update_stats(message.from_user.id, "command")

@dp.message(Command("thoughts_stop"))
async def cmd_thoughts_stop(message: Message):
    if not message.from_user or message.from_user.id != ADMIN_USER_ID:
        await message.reply("❌ Только для админа!")
        return
    daily_thoughts.stop()
    await message.reply("🛑 Мысли остановлены")
    if message.from_user:
        update_stats(message.from_user.id, "command")

@dp.message(Command("thoughts_add"))
async def cmd_thoughts_add(message: Message):
    if not message.from_user or message.from_user.id != ADMIN_USER_ID:
        await message.reply("❌ Только для админа!")
        return
    
    if not message.text:
        await message.reply("❌ Укажите ссылку на чат")
        return
    args = message.text.split(maxsplit=1)
    
    if len(args) > 1:
        link = args[1].strip()
        try:
            if link.startswith("https://t.me/"):
                username = link.replace("https://t.me/", "").split("/")[0]
                chat_username = f"@{username}"
            elif link.startswith("@"):
                chat_username = link
            else:
                await message.reply("❌ Неверный формат")
                return
            
            chat = await bot.get_chat(chat_username)
            if chat and hasattr(chat, 'id'):
                chat_id = chat.id
                chat_title = (chat.title or chat.username or f"Чат {chat_id}") if chat else "Неизвестный чат"
            else:
                await message.reply("❌ Не удалось получить информацию о чате")
                return
            success, msg = daily_thoughts.add_chat(chat_id, chat_title)
            await message.reply(f"{'✅' if success else '⚠️'} {msg}")
        except Exception as e:
            await message.reply(f"❌ Ошибка: {e}")
    else:
            if message.chat:
                chat_id = message.chat.id
                chat_title = message.chat.title or message.chat.username or f"Чат {chat_id}"
                success, msg = daily_thoughts.add_chat(chat_id, chat_title)
                await message.reply(f"{'✅' if success else '⚠️'} {msg}")
            else:
                await message.reply("❌ Не удалось определить чат")
    
    if message.from_user:
        update_stats(message.from_user.id, "command")

@dp.message(Command("thoughts_remove"))
async def cmd_thoughts_remove(message: Message):
    if not message.from_user or message.from_user.id != ADMIN_USER_ID:
        await message.reply("❌ Только для админа!")
        return
    
    if message.chat:
        chat_id = message.chat.id
        success, msg = daily_thoughts.remove_chat(chat_id)
        await message.reply(f"{'✅' if success else '⚠️'} {msg}")
    else:
        await message.reply("❌ Не удалось определить чат")
    update_stats(message.from_user.id, "command")

@dp.message(Command("thoughts_time"))
async def cmd_thoughts_time(message: Message):
    if not message.from_user or message.from_user.id != ADMIN_USER_ID:
        await message.reply("❌ Только для админа!")
        return
    
    if not message.text:
        await message.reply("❌ Использование: /thoughts_time часы минуты")
        return
    args = message.text.split()
    if len(args) < 3:
        await message.reply("❌ Использование: /thoughts_time часы минуты")
        return
    
    try:
        hour = int(args[1])
        minute = int(args[2])
        daily_thoughts.set_time(hour, minute)
        await message.reply(f"✅ Время установлено на {hour:02d}:{minute:02d}")
    except:
        await message.reply("❌ Неверный формат")
    
    if message.from_user:
        update_stats(message.from_user.id, "command")

@dp.message(Command("thoughts_now"))
async def cmd_thoughts_now(message: Message):
    if not message.from_user or message.from_user.id != ADMIN_USER_ID:
        await message.reply("❌ Только для админа!")
        return
    
    await message.reply("🧠 Генерирую мысли...")
    thoughts = await daily_thoughts.get_random_thoughts(5, 10)
    await message.reply("\n".join(thoughts))
    if message.from_user:
        update_stats(message.from_user.id, "command")

@dp.message(Command("thoughts_list"))
async def cmd_thoughts_list(message: Message):
    if not message.from_user or message.from_user.id != ADMIN_USER_ID:
        await message.reply("❌ Только для админа!")
        return
    
    chats = daily_thoughts.get_chats_list()
    if chats:
        text = "📋 **СПИСОК ЧАТОВ**\n\n"
        for i, chat in enumerate(chats, 1):
            text += f"{i}. {chat['title']} (`{chat['id']}`)\n"
        await message.reply(text, parse_mode="Markdown")
    else:
        await message.reply("📭 Список чатов пуст")
    if message.from_user:
        update_stats(message.from_user.id, "command")

# ======== ПОЛИТИКА ========
async def show_policy(message: Message):
    policy_text = (
        "📜 **ПОЛИТИКА БОТА**\n\n"
        "Нажимая «Я согласен», вы подтверждаете согласие с политикой."
    )
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Я согласен", callback_data="accept_policy")
    builder.button(text="📄 Подробнее", url="https://telegra.ph/Politika-bota-AzovoAI-03-06")
    await message.answer(policy_text, reply_markup=builder.as_markup(), parse_mode="Markdown")

@dp.callback_query(F.data == "accept_policy")
async def accept_policy(callback: CallbackQuery):
    if callback.from_user:
        set_user_consent(callback.from_user.id)
    if callback.message is not None:
        msg = cast(Message, callback.message)
        await msg.edit_text(
            "✅ Доступ открыт!\n\n"
            "Команды:\n"
            "/bot - статистика\n"
            "/ping - задержка\n\n"
            "Просто пиши, отвечу"
        )
    await callback.answer()

# ======== СТАРТ ========

@dp.message(CommandStart())
async def start(message: Message):
    if not message.from_user or not message.chat:
        return
    if not has_user_consent(message.from_user.id):
        await show_policy(message)
        return
    
    keyboard = get_add_to_group_keyboard()
    await message.answer(
        "привет я новая нейросеть по имени азovoAI\n"
        "если че мое имя не связана с политикой или селом в Омской областе\n"
        "мой тгк - https://t.me/azovo_AI\n"
        "тгк моего владельца - https://t.me/SOBKA_TV\n"
        "добавь меня в свой чат",
        reply_markup=keyboard,
    )
    update_stats(message.from_user.id, "command")

def get_add_to_group_keyboard():
    builder = InlineKeyboardBuilder()
    bot_username = BOT_USERNAME.lstrip('@')
    add_link = f"https://t.me/{bot_username}?startgroup=true"
    builder.button(text="➕ Добавить в чат", url=add_link)
    return builder.as_markup()

@dp.message(Command("queue"))
async def queue_status(message: Message):
    if not message.from_user:
        await message.reply("❌ Не удалось определить пользователя")
        return
    if not has_user_consent(message.from_user.id) and message.chat and message.chat.type == "private":
        await show_policy(message)
        return
    pos = None
    try:
        for i in range(request_queue.qsize()):
            try:
                queued_msg, _ = request_queue._queue[i]  # type: ignore
                if queued_msg and queued_msg.from_user and queued_msg.from_user.id == message.from_user.id:
                    pos = i + 1
                    break
            except (IndexError, TypeError, AttributeError):
                continue
    except (IndexError, AttributeError, ValueError):
        pass
    await message.answer(f"Позиция: {pos}" if pos else "Тебя нет в очереди")
    update_stats(message.from_user.id, "command")

# ======== ОБРАБОТЧИК СООБЩЕНИЙ ========

@dp.message()
async def handle_message(message: Message):
    if not message.from_user or not message.chat:
        return
    user_id = message.from_user.id
    
    if message.text and message.text.startswith(tuple(f'/{cmd}' for cmd in BOT_COMMANDS)):
        return
    
    if not message.text:
        return
    
    if not should_respond(message):
        return
    
    if is_blacklisted(message.text):
        return
    
    now = time.time()
    if now - user_last_time[user_id] < RATE_LIMIT_SECONDS:
        await message.reply("не флуди")
        return
    user_last_time[user_id] = now
    
    loop = asyncio.get_running_loop()
    queue_size = request_queue.qsize()
    await request_queue.put((message, loop))
    
    if queue_size > 0:
        await notify_queue_position(message, queue_size + 1)

# ======== ЗАПУСК ========

async def on_startup():
    asyncio.create_task(queue_processor())
    global stats
    stats["last_restart"] = int(time.time())
    save_stats(stats)
    
    print(f"✅ Бот запущен!")
    print(f"🤖 Используется модель: {MODEL_NAME}")
    print(f"📁 Датасет: {DATASET_FILE} (только для статистики)")

async def main():
    try:
        dp.startup.register(on_startup)
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("🛑 Бот остановлен")