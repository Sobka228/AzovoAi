
"""
Telegram Bot with Message Processing
"""

import os
import sys
import asyncio
import time
import random
import json
import logging
import datetime
import warnings
from collections import defaultdict
from typing import cast, Optional, Dict, List, Tuple

import requests
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, CallbackQuery, ReactionTypeEmoji
from aiogram.enums import ChatAction
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv

# Configuration
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
warnings.filterwarnings("ignore")

load_dotenv()

# Bot Configuration
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable not set")

# Pollinations.ai configuration
POLLINATIONS_URL = "https://text.pollinations.ai/"
POLLINATIONS_MODEL = os.getenv("POLLINATIONS_MODEL", "openai")

DATASET_FILE = "dataset.txt"
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "7451061064"))
RATE_LIMIT_SECONDS = 2
BOT_USERNAME = os.getenv("BOT_USERNAME", "azovoAIbot")
PORT = int(os.getenv("PORT", "10000"))

# Storage files
STATS_FILE = "bot_stats.json"
CONSENT_FILE = "user_consent.json"
BLACKLIST_FILE = "blacklist.json"

# Trigger words
TRIGGER_WORDS = ["азово", "azovo", f"@{BOT_USERNAME.lower()}"]
BOT_START_TIME = int(time.time())

# Initialize bot and dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Reactions
TELEGRAM_REACTIONS = ["👍", "👎", "❤️", "🔥", "🥰", "👏", "😁", "🤔", "🤯", "😱", "🎉", "🤩", "🥺", "🤡", "💩"]

REACTION_KEYWORDS = [
    "поставь реакцию", "реакцию поставь", "поставь рандомную реакцию",
    "поставь любую реакцию", "поставь смайлик", "оцени", "прореагируй",
    "сделай реакцию", "реакцию", "поставь 👍", "поставь ❤️", "поставь 🔥",
    "поставь 🥚", "поставь 😱", "реакция"
]

REACTION_MAP: Dict[str, str] = {
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
    'reset', 'queue', 'start', 'bot', 'ping', 'save', 'dataset_stats',
    'clear_dataset', 'export_dataset', 'thoughts_start', 'thoughts_stop',
    'thoughts_add', 'thoughts_remove', 'thoughts_time', 'thoughts_now', 'thoughts_list'
]

DEFAULT_BLACKLIST = ["пах", "пax"]

# ============================================================================
# Blacklist Management
# ============================================================================

def load_blacklist() -> List[str]:
    """Load blacklist from file or return default."""
    if os.path.exists(BLACKLIST_FILE):
        try:
            with open(BLACKLIST_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get("words", [])
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load blacklist: {e}")
            return DEFAULT_BLACKLIST.copy()
    else:
        save_blacklist(DEFAULT_BLACKLIST)
        return DEFAULT_BLACKLIST.copy()


def save_blacklist(words: List[str]) -> None:
    """Save blacklist to file."""
    try:
        with open(BLACKLIST_FILE, 'w', encoding='utf-8') as f:
            json.dump({"words": words}, f, ensure_ascii=False, indent=2)
    except IOError as e:
        logger.error(f"Failed to save blacklist: {e}")


def is_blacklisted(text: str) -> bool:
    """Check if text contains blacklisted words."""
    if not text:
        return False
    text_lower = text.lower()
    words = load_blacklist()
    return any(word in text_lower for word in words)


# ============================================================================
# User Consent Management
# ============================================================================

def load_consent() -> Dict:
    """Load user consent data from file."""
    if os.path.exists(CONSENT_FILE):
        try:
            with open(CONSENT_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load consent data: {e}")
            return {}
    return {}


def save_consent(consent_data: Dict) -> None:
    """Save user consent data to file."""
    try:
        with open(CONSENT_FILE, 'w', encoding='utf-8') as f:
            json.dump(consent_data, f, ensure_ascii=False, indent=2)
    except IOError as e:
        logger.error(f"Failed to save consent data: {e}")


def has_user_consent(user_id: int) -> bool:
    """Check if user has given consent."""
    consent_data = load_consent()
    return str(user_id) in consent_data


def set_user_consent(user_id: int) -> None:
    """Record user consent."""
    consent_data = load_consent()
    consent_data[str(user_id)] = {
        "consent_time": int(time.time()),
        "consent_version": "1.0"
    }
    save_consent(consent_data)

# ============================================================================
# Statistics Management
# ============================================================================

def load_stats() -> Dict:
    """Load statistics from file."""
    if os.path.exists(STATS_FILE):
        try:
            with open(STATS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if "users" in data and "total_messages" in data:
                    return data
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load stats: {e}")
    return get_default_stats()


def save_stats(stats_data: Dict) -> bool:
    """Save statistics to file."""
    try:
        with open(STATS_FILE, 'w', encoding='utf-8') as f:
            json.dump(stats_data, f, ensure_ascii=False, indent=2)
        return True
    except IOError as e:
        logger.error(f"Failed to save stats: {e}")
        return False


def get_default_stats() -> Dict:
    """Return default statistics structure."""
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


def update_stats(user_id: int, message_type: str = "message") -> None:
    """Update statistics with new message."""
    global stats
    user_id_str = str(user_id)
    stats["total_messages"] += 1
    
    if message_type == "command":
        stats["total_commands"] += 1
    elif message_type == "thought":
        stats["total_thoughts"] += 1
    
    if user_id_str not in stats["users"]:
        stats["users"][user_id_str] = {
            "first_seen": int(time.time()),
            "messages_count": 0,
            "commands_count": 0,
            "thoughts_count": 0
        }
    
    stats["users"][user_id_str]["messages_count"] += 1
    if message_type == "command":
        stats["users"][user_id_str]["commands_count"] += 1
    elif message_type == "thought":
        stats["users"][user_id_str]["thoughts_count"] += 1
    
    save_stats(stats)

# ============================================================================
# Message Queue and Rate Limiting
# ============================================================================

request_queue: asyncio.Queue = asyncio.Queue()
user_last_time: Dict[int, float] = defaultdict(float)


def is_after_start(message: Message) -> bool:
    """Check if message was sent after bot started."""
    message_time = int(message.date.timestamp())
    return message_time >= BOT_START_TIME


async def notify_queue_position(message: Message, position: int) -> None:
    """Notify user of their position in message queue."""
    await message.answer(f"Ты в очереди. Позиция: {position}. Жди.")


# ============================================================================
# Content Safety and Filtering
# ============================================================================

def is_safe_text(text: str) -> bool:
    """Check if text contains harmful content."""
    if not text:
        return True
    text_lower = text.lower()
    banned_words = ["cp", "child porn", "детское порно"]
    return not any(word in text_lower for word in banned_words)


def should_respond(message: Message) -> bool:
    """Determine if bot should respond to message."""
    if not message.chat or not message.from_user:
        return False
    
    # Check consent for private chats
    if message.chat.type == "private" and not has_user_consent(message.from_user.id):
        return False
    
    # Check if message is after bot start
    if not is_after_start(message):
        return False
    
    # Always respond in private chats with consent
    if message.chat.type == "private":
        return True
    
    # In group chats, check for triggers
    if not message.text:
        return False
    
    text_lower = message.text.lower()
    
    # Check for bot mention
    if f"@{BOT_USERNAME.lower()}" in text_lower:
        return True
    
    # Check for trigger words
    for word in TRIGGER_WORDS:
        if word in text_lower:
            return True
    
    # Check if replying to bot message
    if (message.reply_to_message and 
        message.reply_to_message.from_user and 
        message.reply_to_message.from_user.id == bot.id):
        return True
    
    return False

# ============================================================================
# Dataset Management
# ============================================================================

def read_dataset() -> List[str]:
    """Read all lines from dataset file."""
    if not os.path.exists(DATASET_FILE):
        return []
    try:
        with open(DATASET_FILE, "r", encoding="utf-8") as f:
            return [line.strip() for line in f.readlines() if line.strip()]
    except IOError as e:
        logger.error(f"Failed to read dataset: {e}")
        return []


def append_to_dataset(text: str) -> None:
    """Append text to dataset if it's safe."""
    if is_safe_text(text):
        try:
            with open(DATASET_FILE, "a", encoding="utf-8") as f:
                f.write(text.strip() + "\n")
        except IOError as e:
            logger.error(f"Failed to write to dataset: {e}")


def get_dataset_size() -> int:
    """Get number of lines in dataset."""
    if not os.path.exists(DATASET_FILE):
        return 0
    try:
        with open(DATASET_FILE, "r", encoding="utf-8") as f:
            return len(f.readlines())
    except IOError as e:
        logger.error(f"Failed to get dataset size: {e}")
        return 0


def get_dataset_content() -> str:
    """Get full content of dataset file."""
    if not os.path.exists(DATASET_FILE):
        return "Dataset is empty"
    try:
        with open(DATASET_FILE, "r", encoding="utf-8") as f:
            return f.read()
    except IOError as e:
        logger.error(f"Failed to read dataset content: {e}")
        return "Failed to read dataset"


def convert_to_train_format() -> List[Tuple[str, str]]:
    """Convert dataset to paired format for training."""
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


# ============================================================================
# Reaction Detection and Handling
# ============================================================================

async def check_and_set_reaction(message: Message) -> bool:
    """Check if message requests reaction and set one if needed."""
    if not message.text:
        return False
    
    text_lower = message.text.lower().strip()
    is_reaction_request = any(keyword in text_lower for keyword in REACTION_KEYWORDS)
    
    if not is_reaction_request:
        return False
    
    # Find reaction based on keywords
    reaction = None
    for word, emoji in REACTION_MAP.items():
        if word in text_lower:
            reaction = emoji
            break
    
    # Use random reaction if none matched
    if not reaction:
        reaction = random.choice(TELEGRAM_REACTIONS)
    
    try:
        await message.react([ReactionTypeEmoji(emoji=reaction)])
        return True
    except Exception as e:
        logger.warning(f"Failed to set reaction: {e}")
        return False

# System prompt
SYSTEM_PROMPT = (
    "ты хам ебаный отвечай коротко и с маленькой буквы без знаков препинания "
    "матерись как сапожник если чел норм отвечай хамовато если чел хамит в ответ "
    "хами еще сильнее иногда сходи с ума пиши рандомные хуйни про яйца батарейки "
    "крону зверя в проводах пукизм и азово если чел достал пошли нахуй если чел "
    "грубит ответь еще грубее никогда не извиняйся не будь вежливым вообще никаких "
    "знаков препинания только буквы и маты и с маленькой буквы"
)

# ============================================================================
# Model Inference
# ============================================================================

def ask_ai(user_text: str) -> str:
    """Call Pollinations.ai API with user input."""
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
                # Or check for other response keys
                for key in ("text", "response", "content", "output"):
                    if key in data:
                        return str(data[key]).strip()
        except (json.JSONDecodeError, KeyError, IndexError):
            pass

        return text if text else "нихуя не понял"

    except requests.Timeout:
        logger.error("Pollinations API timeout")
        return "таймаут блять попробуй позже"
    except requests.ConnectionError:
        logger.error("Pollinations API connection error")
        return "нет связи с мозгами попробуй позже"
    except Exception as e:
        logger.exception("ask_ai error")
        return f"всё упало: {e}"


# ============================================================================
# Message Queue Processing
# ============================================================================

async def queue_processor() -> None:
    """Process messages from queue sequentially."""
    while True:
        try:
            msg, loop = await request_queue.get()
            
            try:
                await bot.send_chat_action(chat_id=msg.chat.id, action=ChatAction.TYPING)

                if msg.photo:
                    reply = "Пока не обрабатываю фото"
                    append_to_dataset(f"USER: [PHOTO] {msg.caption or ''}")
                    append_to_dataset(f"ASSISTANT: {reply}")
                    await msg.reply(reply)
                    if msg.from_user:
                        update_stats(msg.from_user.id, "message")
                else:
                    # Skip if message is a command
                    if msg.text and msg.text.startswith(tuple(f'/{cmd}' for cmd in BOT_COMMANDS)):
                        request_queue.task_done()
                        continue
                    
                    # Check for reaction request
                    reaction_result = await check_and_set_reaction(msg)
                    if reaction_result:
                        request_queue.task_done()
                        continue
                    
                    # Generate response
                    if msg.text:
                        reply = await loop.run_in_executor(None, ask_ai, msg.text)
                        append_to_dataset(f"USER: {msg.text}")
                        append_to_dataset(f"ASSISTANT: {reply}")
                        await msg.reply(reply)
                        if msg.from_user:
                            update_stats(msg.from_user.id, "message")
                        
            except Exception as e:
                logger.error(f"Queue processing error: {e}")
                await msg.reply(f"Ошибка: {e}")
            finally:
                request_queue.task_done()
        except Exception as e:
            logger.error(f"Unexpected queue error: {e}")
            await asyncio.sleep(1)

# ============================================================================
# Scheduled Message System
# ============================================================================

class ScheduledMessenger:
    """Manages scheduled message generation and delivery."""
    
    def __init__(self, bot_instance: Bot):
        self.bot = bot_instance
        self.is_running = False
        self.task: Optional[asyncio.Task] = None
        self.target_chats: List[Dict] = []
        self.hour = 12
        self.minute = 0
    
    def add_chat(self, chat_id: int, chat_title: str) -> Tuple[bool, str]:
        """Add chat to scheduled messaging list."""
        for chat in self.target_chats:
            if chat["id"] == chat_id:
                return False, "Chat already in list"
        
        self.target_chats.append({
            "id": chat_id,
            "title": chat_title,
            "added_at": time.time()
        })
        return True, f"Chat '{chat_title}' added"
    
    def remove_chat(self, chat_id: int) -> Tuple[bool, str]:
        """Remove chat from scheduled messaging list."""
        for i, chat in enumerate(self.target_chats):
            if chat["id"] == chat_id:
                title = chat['title']
                self.target_chats.pop(i)
                return True, f"Chat '{title}' removed"
        return False, "Chat not found"
    
    def remove_chat_by_index(self, index: int) -> Tuple[bool, str]:
        """Remove chat by list index."""
        if 0 <= index < len(self.target_chats):
            chat = self.target_chats.pop(index)
            return True, f"Chat '{chat['title']}' removed"
        return False, "Invalid index"
    
    def set_time(self, hour: int, minute: int) -> None:
        """Set scheduled message time."""
        self.hour = hour
        self.minute = minute
    
    async def generate_message(self) -> str:
        """Generate a message using the model."""
        prompts = [
            "Напиши случайную фразу",
            "Что-то оригинальное",
            "Интересная мысль",
            "Смешная шутка",
            "Что-то неожиданное"
        ]
        prompt = random.choice(prompts)
        
        try:
            loop = asyncio.get_running_loop()
            message = await loop.run_in_executor(None, ask_ai, prompt)
            if len(message) > 200:
                message = message[:200] + "..."
            return message
        except Exception as e:
            logger.error(f"Failed to generate message: {e}")
            return "Не получилось сгенерировать"
    
    async def get_random_messages(self, min_count: int = 3, max_count: int = 7) -> List[str]:
        """Generate multiple random messages."""
        count = random.randint(min_count, max_count)
        result = []
        for i in range(count):
            msg = await self.generate_message()
            result.append(f"{i+1}. {msg}")
            await asyncio.sleep(1)
        return result
    
    async def send_scheduled_messages(self) -> None:
        """Send scheduled messages to all registered chats."""
        if not self.target_chats:
            return
        
        messages = await self.get_random_messages()
        text = "📬 Обновления\n\n" + "\n".join(messages)
        
        for chat in self.target_chats:
            try:
                await self.bot.send_message(chat_id=chat["id"], text=text, parse_mode="Markdown")
                update_stats(ADMIN_USER_ID, "thought")
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Failed to send message to {chat['id']}: {e}")
    
    async def daily_loop(self) -> None:
        """Main scheduling loop."""
        while self.is_running:
            now = datetime.datetime.now()
            target_time = now.replace(hour=self.hour, minute=self.minute, second=0, microsecond=0)
            
            if now > target_time:
                target_time = target_time.replace(day=target_time.day + 1)
            
            wait_seconds = (target_time - now).total_seconds()
            await asyncio.sleep(wait_seconds)
            
            if self.is_running:
                await self.send_scheduled_messages()
    
    def start(self) -> None:
        """Start the scheduler."""
        if not self.is_running:
            self.is_running = True
            self.task = asyncio.create_task(self.daily_loop())
            logger.info("Scheduler started")
    
    def stop(self) -> None:
        """Stop the scheduler."""
        self.is_running = False
        if self.task:
            self.task.cancel()
            logger.info("Scheduler stopped")
    
    def get_chats_list(self) -> List[Dict]:
        """Get list of registered chats."""
        return self.target_chats


scheduled_messenger = ScheduledMessenger(bot)

# ============================================================================
# Admin Commands
# ============================================================================

@dp.message(Command("save"))
async def cmd_save(message: Message) -> None:
    """Handle /save command to verify and log dataset state (admin only)."""
    if not message.from_user or message.from_user.id != ADMIN_USER_ID:
        await message.reply("❌ Admin only")
        return
    
    try:
        dataset_lines = read_dataset()
        current_size = len(dataset_lines)
        
        await message.reply(
            f"💾 Dataset State\n\n"
            f"Total entries: {current_size}\n"
            f"File: `{DATASET_FILE}`",
            parse_mode="Markdown"
        )
        update_stats(message.from_user.id, "command")
        append_to_dataset(f"ADMIN: Checked dataset ({current_size} entries)")
        logger.info(f"Admin verified dataset: {current_size} entries")
    except Exception as e:
        logger.error(f"Error in cmd_save: {e}")
        await message.reply("❌ Error processing command")


@dp.message(Command("ping"))
async def cmd_ping(message: Message) -> None:
    """Handle /ping command to check bot responsiveness and uptime."""
    try:
        start_time = time.time()
        msg = await message.reply("🏓 Checking...")
        end_time = time.time()
        ping_ms = round((end_time - start_time) * 1000, 2)
        
        uptime_seconds = int(time.time() - stats.get("last_restart", time.time()))
        uptime_str = str(datetime.timedelta(seconds=uptime_seconds))
        
        await msg.edit_text(
            f"🏓 Bot Status\n\n"
            f"Response time: {ping_ms} ms\n"
            f"Uptime: {uptime_str}\n"
            f"Model: `{POLLINATIONS_MODEL} (Pollinations.ai)`",
            parse_mode="Markdown"
        )
        
        if message.from_user:
            update_stats(message.from_user.id, "command")
            logger.info(f"Ping command from {message.from_user.id}: {ping_ms}ms")
    except Exception as e:
        logger.error(f"Error in cmd_ping: {e}")
        await message.reply("❌ Error processing command")

@dp.message(Command("reset"))
async def reset_chat(message: Message) -> None:
    """Handle /reset command to clear chat memory (admin only)."""
    if not message.from_user or message.from_user.id != ADMIN_USER_ID:
        await message.reply("❌ Admin only")
        return
    
    try:
        await message.reply("🧹 Memory cleared")
        append_to_dataset("ADMIN: Cleared memory")
        if message.from_user:
            update_stats(message.from_user.id, "command")
            logger.info(f"Memory cleared by admin {message.from_user.id}")
    except Exception as e:
        logger.error(f"Error in reset_chat: {e}")
        await message.reply("❌ Error processing command")


@dp.message(Command("bot"))
async def bot_stats(message: Message) -> None:
    """Handle /bot command to display bot statistics."""
    if not message.from_user or not message.chat:
        return
    
    try:
        if not has_user_consent(message.from_user.id) and message.chat.type == "private":
            await show_policy(message)
            return
        
        current_time = int(time.time())
        uptime = current_time - stats.get("last_restart", current_time)
        uptime_days = uptime // 86400
        uptime_hours = (uptime % 86400) // 3600
        uptime_minutes = (uptime % 3600) // 60
        
        dataset_size = get_dataset_size()
        pairs = convert_to_train_format()
        unique_users = len(stats.get("users", {}))
        
        text = (
            f"🤖 Bot Statistics\n\n"
            f"Messages: {stats.get('total_messages', 0)}\n"
            f"Commands: {stats.get('total_commands', 0)}\n"
            f"Dataset: {dataset_size} entries, {len(pairs)} pairs\n"
            f"Users: {unique_users}\n"
            f"Uptime: {uptime_days}d {uptime_hours}h {uptime_minutes}m\n"
            f"Model: `{POLLINATIONS_MODEL} (Pollinations.ai)`"
        )
        await message.reply(text, parse_mode="Markdown")
        if message.from_user:
            update_stats(message.from_user.id, "command")
            logger.info(f"Stats requested by {message.from_user.id}")
    except Exception as e:
        logger.error(f"Error in bot_stats: {e}")
        await message.reply("❌ Error processing command")


@dp.message(Command("dataset_stats"))
async def cmd_dataset_stats(message: Message) -> None:
    """Handle /dataset_stats command to display dataset statistics (admin only)."""
    if not message.from_user or message.from_user.id != ADMIN_USER_ID:
        await message.reply("❌ Admin only")
        return
    
    try:
        dataset_size = get_dataset_size()
        pairs = convert_to_train_format()
        
        text = (
            f"📊 Dataset Statistics\n\n"
            f"Entries: {dataset_size}\n"
            f"Pairs: {len(pairs)}\n"
            f"File: `{DATASET_FILE}`"
        )
        await message.reply(text, parse_mode="Markdown")
        if message.from_user:
            update_stats(message.from_user.id, "command")
            logger.info(f"Dataset stats requested by {message.from_user.id}")
    except Exception as e:
        logger.error(f"Error in cmd_dataset_stats: {e}")
        await message.reply("❌ Error processing command")


@dp.message(Command("clear_dataset"))
async def cmd_clear_dataset(message: Message) -> None:
    """Handle /clear_dataset command to clear the dataset (admin only)."""
    if not message.from_user or message.from_user.id != ADMIN_USER_ID:
        await message.reply("❌ Admin only")
        return
    
    try:
        with open(DATASET_FILE, "w", encoding="utf-8") as f:
            f.write("")
        
        await message.reply("🗑️ Dataset cleared")
        if message.from_user:
            update_stats(message.from_user.id, "command")
            logger.info(f"Dataset cleared by admin {message.from_user.id}")
    except IOError as e:
        logger.error(f"IO error in cmd_clear_dataset: {e}")
        await message.reply("❌ Error clearing dataset")
    except Exception as e:
        logger.error(f"Error in cmd_clear_dataset: {e}")
        await message.reply("❌ Error processing command")


@dp.message(Command("export_dataset"))
async def cmd_export_dataset(message: Message) -> None:
    """Handle /export_dataset command to export dataset as file (admin only)."""
    if not message.from_user or message.from_user.id != ADMIN_USER_ID:
        await message.reply("❌ Admin only")
        return
    
    try:
        dataset_content = get_dataset_content()
        dataset_size = get_dataset_size()
        pairs = convert_to_train_format()
        
        if len(dataset_content) > 4000:
            # Export large datasets as file
            temp_file = f"dataset_export_{int(time.time())}.txt"
            try:
                with open(temp_file, "w", encoding="utf-8") as f:
                    f.write(dataset_content)
                
                with open(temp_file, "rb") as f:
                    await message.reply_document(
                        types.FSInputFile(temp_file),
                        caption=(
                            f"Dataset Export\n"
                            f"Entries: {dataset_size}\n"
                            f"Pairs: {len(pairs)}"
                        )
                    )
                logger.info(f"Dataset exported by admin {message.from_user.id}: {dataset_size} entries")
            finally:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
        else:
            # Send small datasets as text
            await message.reply(
                f"📁 Dataset Content\n\n"
                f"Entries: {dataset_size}\n"
                f"Pairs: {len(pairs)}\n\n"
                f"```\n{dataset_content}\n```",
                parse_mode="Markdown"
            )
        
        if message.from_user:
            update_stats(message.from_user.id, "command")
    except IOError as e:
        logger.error(f"IO error in cmd_export_dataset: {e}")
        await message.reply("❌ Error exporting dataset")
    except Exception as e:
        logger.error(f"Error in cmd_export_dataset: {e}")
        await message.reply("❌ Error processing command")


# ============================================================================
# Scheduler Commands
# ============================================================================

@dp.message(Command("thoughts_start"))
async def cmd_thoughts_start(message: Message) -> None:
    """Handle /thoughts_start command to enable scheduled messages (admin only)."""
    if not message.from_user or message.from_user.id != ADMIN_USER_ID:
        await message.reply("❌ Admin only")
        return
    
    try:
        scheduled_messenger.start()
        await message.reply(
            f"✅ Scheduler started\n"
            f"Time: {scheduled_messenger.hour:02d}:{scheduled_messenger.minute:02d}"
        )
        if message.from_user:
            update_stats(message.from_user.id, "command")
            logger.info(f"Scheduler started by admin {message.from_user.id}")
    except Exception as e:
        logger.error(f"Error in cmd_thoughts_start: {e}")
        await message.reply("❌ Error starting scheduler")


@dp.message(Command("thoughts_stop"))
async def cmd_thoughts_stop(message: Message) -> None:
    """Handle /thoughts_stop command to disable scheduled messages (admin only)."""
    if not message.from_user or message.from_user.id != ADMIN_USER_ID:
        await message.reply("❌ Admin only")
        return
    
    try:
        scheduled_messenger.stop()
        await message.reply("🛑 Scheduler stopped")
        if message.from_user:
            update_stats(message.from_user.id, "command")
            logger.info(f"Scheduler stopped by admin {message.from_user.id}")
    except Exception as e:
        logger.error(f"Error in cmd_thoughts_stop: {e}")
        await message.reply("❌ Error stopping scheduler")


@dp.message(Command("thoughts_add"))
async def cmd_thoughts_add(message: Message) -> None:
    """Handle /thoughts_add command to add group to scheduler (admin only)."""
    if not message.from_user or message.from_user.id != ADMIN_USER_ID:
        await message.reply("❌ Admin only")
        return
    
    try:
        if not message.text:
            await message.reply("❌ Specify chat link")
            return
        
        args = message.text.split(maxsplit=1)
        
        if len(args) > 1:
            link = args[1].strip()
            try:
                # Parse link or username
                if link.startswith("https://t.me/"):
                    username = link.replace("https://t.me/", "").split("/")[0]
                    chat_username = f"@{username}"
                elif link.startswith("@"):
                    chat_username = link
                else:
                    await message.reply("❌ Invalid format")
                    return
                
                chat = await bot.get_chat(chat_username)
                if chat and hasattr(chat, 'id'):
                    chat_id = chat.id
                    chat_title = (chat.title or chat.username or f"Chat {chat_id}") if chat else "Unknown"
                else:
                    await message.reply("❌ Failed to get chat info")
                    return
                
                success, result_text = scheduled_messenger.add_chat(chat_id, chat_title)
                await message.reply(f"{'✅' if success else '⚠️'} {result_text}")
                if success:
                    logger.info(f"Chat {chat_id} added to scheduler by admin {message.from_user.id}")
            except Exception as e:
                logger.error(f"Error parsing chat link: {e}")
                await message.reply(f"❌ Error: {e}")
        else:
            # Use current chat
            if message.chat:
                chat_id = message.chat.id
                chat_title = message.chat.title or message.chat.username or f"Chat {chat_id}"
                success, result_text = scheduled_messenger.add_chat(chat_id, chat_title)
                await message.reply(f"{'✅' if success else '⚠️'} {result_text}")
                if success:
                    logger.info(f"Chat {chat_id} added to scheduler by admin")
            else:
                await message.reply("❌ Failed to identify chat")
        
        if message.from_user:
            update_stats(message.from_user.id, "command")
    except Exception as e:
        logger.error(f"Error in cmd_thoughts_add: {e}")
        await message.reply("❌ Error processing command")


@dp.message(Command("thoughts_remove"))
async def cmd_thoughts_remove(message: Message) -> None:
    """Handle /thoughts_remove command to remove group from scheduler (admin only)."""
    if not message.from_user or message.from_user.id != ADMIN_USER_ID:
        await message.reply("❌ Admin only")
        return
    
    try:
        if message.chat:
            chat_id = message.chat.id
            success, result_text = scheduled_messenger.remove_chat(chat_id)
            await message.reply(f"{'✅' if success else '⚠️'} {result_text}")
            if success:
                logger.info(f"Chat {chat_id} removed from scheduler by admin")
        else:
            await message.reply("❌ Failed to identify chat")
        
        if message.from_user:
            update_stats(message.from_user.id, "command")
    except Exception as e:
        logger.error(f"Error in cmd_thoughts_remove: {e}")
        await message.reply("❌ Error processing command")


@dp.message(Command("thoughts_time"))
async def cmd_thoughts_time(message: Message) -> None:
    """Handle /thoughts_time command to set scheduler time (admin only)."""
    if not message.from_user or message.from_user.id != ADMIN_USER_ID:
        await message.reply("❌ Admin only")
        return
    
    try:
        if not message.text:
            await message.reply("❌ Usage: /thoughts_time hours minutes")
            return
        
        args = message.text.split()
        if len(args) < 3:
            await message.reply("❌ Usage: /thoughts_time hours minutes")
            return
        
        try:
            hour = int(args[1])
            minute = int(args[2])
            
            if not (0 <= hour < 24 and 0 <= minute < 60):
                await message.reply("❌ Invalid time (hour: 0-23, minute: 0-59)")
                return
            
            scheduled_messenger.set_time(hour, minute)
            await message.reply(f"✅ Scheduler time set to {hour:02d}:{minute:02d}")
            logger.info(f"Scheduler time changed to {hour:02d}:{minute:02d} by admin {message.from_user.id}")
        except ValueError:
            await message.reply("❌ Invalid format (expected integers)")
        
        if message.from_user:
            update_stats(message.from_user.id, "command")
    except Exception as e:
        logger.error(f"Error in cmd_thoughts_time: {e}")
        await message.reply("❌ Error processing command")


@dp.message(Command("thoughts_now"))
async def cmd_thoughts_now(message: Message) -> None:
    """Handle /thoughts_now command to generate messages immediately (admin only)."""
    if not message.from_user or message.from_user.id != ADMIN_USER_ID:
        await message.reply("❌ Admin only")
        return
    
    try:
        await message.reply("🧠 Generating messages...")
        messages = await scheduled_messenger.get_random_messages(5, 10)
        
        text = "Generated Messages:\n\n" + "\n".join(messages)
        await message.reply(text)
        
        if message.from_user:
            update_stats(message.from_user.id, "command")
            logger.info(f"Messages generated on-demand by admin {message.from_user.id}")
    except Exception as e:
        logger.error(f"Error in cmd_thoughts_now: {e}")
        await message.reply("❌ Error generating messages")


@dp.message(Command("thoughts_list"))
async def cmd_thoughts_list(message: Message) -> None:
    """Handle /thoughts_list command to show scheduled groups (admin only)."""
    if not message.from_user or message.from_user.id != ADMIN_USER_ID:
        await message.reply("❌ Admin only")
        return
    
    try:
        chats = scheduled_messenger.get_chats_list()
        if chats:
            text = "📋 Scheduled Groups\n\n"
            for i, chat in enumerate(chats, 1):
                text += f"{i}. {chat['title']} (`{chat['id']}`)\n"
            await message.reply(text, parse_mode="Markdown")
        else:
            await message.reply("📭 No groups scheduled")
        
        if message.from_user:
            update_stats(message.from_user.id, "command")
            logger.info(f"Groups list requested by admin {message.from_user.id}")
    except Exception as e:
        logger.error(f"Error in cmd_thoughts_list: {e}")
        await message.reply("❌ Error processing command")


# ======== ПОЛИТИКА ========
# ============================================================================
# Policy and Consent Management
# ============================================================================

async def show_policy(message: Message) -> None:
    """Display privacy policy with consent options."""
    policy_text = (
        "📜 Privacy Policy\n\n"
        "By clicking 'I Agree', you confirm acceptance of our terms."
    )
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ I Agree", callback_data="accept_policy")
    builder.button(text="📄 Details", url="https://telegra.ph/Politika-bota-AzovoAI-03-06")
    await message.answer(policy_text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    logger.info(f"Policy shown to user {message.from_user.id if message.from_user else 'unknown'}")


@dp.callback_query(F.data == "accept_policy")
async def accept_policy(callback: CallbackQuery) -> None:
    """Handle policy acceptance callback."""
    try:
        if callback.from_user:
            set_user_consent(callback.from_user.id)
            logger.info(f"Policy accepted by user {callback.from_user.id}")
        
        if callback.message is not None:
            msg = cast(Message, callback.message)
            await msg.edit_text(
                "✅ Access granted\n\n"
                "Commands:\n"
                "/bot - Statistics\n"
                "/ping - Response time\n\n"
                "Just send a message to chat with the bot"
            )
        
        await callback.answer("✅ Consent registered")
    except Exception as e:
        logger.error(f"Error in accept_policy: {e}")
        await callback.answer("❌ Error processing choice")


# ============================================================================
# Main Command and Message Handlers
# ============================================================================

@dp.message(CommandStart())
async def start(message: Message) -> None:
    """Handle /start command and show welcome message."""
    if not message.from_user or not message.chat:
        return
    
    try:
        if not has_user_consent(message.from_user.id):
            await show_policy(message)
            return
        
        keyboard = get_add_to_group_keyboard()
        await message.answer(
            "Welcome to AI Bot\n\n"
            "This is an AI assistant bot.\n"
            "Add me to your group chat for intelligent responses.\n\n"
            "Available: /bot (stats), /ping (status)\n"
            "Just write to start chatting.",
            reply_markup=keyboard,
        )
        update_stats(message.from_user.id, "command")
        logger.info(f"Start command from {message.from_user.id}")
    except Exception as e:
        logger.error(f"Error in start: {e}")


def get_add_to_group_keyboard() -> types.InlineKeyboardMarkup:
    """Generate inline keyboard for adding bot to group."""
    builder = InlineKeyboardBuilder()
    bot_username = BOT_USERNAME.lstrip('@')
    add_link = f"https://t.me/{bot_username}?startgroup=true"
    builder.button(text="➕ Add to Group", url=add_link)
    return builder.as_markup()


@dp.message(Command("queue"))
async def queue_status(message: Message) -> None:
    """Handle /queue command to check position in processing queue."""
    if not message.from_user:
        await message.reply("❌ Failed to identify user")
        return
    
    try:
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
        
        if pos:
            await message.answer(f"Queue position: {pos}")
        else:
            await message.answer("You are not in the queue")
        
        update_stats(message.from_user.id, "command")
        logger.info(f"Queue check by {message.from_user.id}")
    except Exception as e:
        logger.error(f"Error in queue_status: {e}")
        await message.reply("❌ Error checking queue")


# ============================================================================
# Main Message Handler
# ============================================================================

@dp.message()
async def handle_message(message: Message) -> None:
    """Main handler for user messages."""
    if not message.from_user or not message.chat:
        return
    
    try:
        user_id = message.from_user.id
        
        # Skip if message is a command (handled by command handlers)
        if message.text and message.text.startswith(tuple(f'/{cmd}' for cmd in BOT_COMMANDS)):
            return
        
        # Skip if no text content
        if not message.text:
            return
        
        # Check if bot should respond to this message
        if not should_respond(message):
            return
        
        # Check if text is blacklisted
        if is_blacklisted(message.text):
            logger.warning(f"Blacklisted text from {user_id}: {message.text[:50]}")
            return
        
        # Rate limiting
        now = time.time()
        if now - user_last_time.get(user_id, 0) < RATE_LIMIT_SECONDS:
            await message.reply("Please don't spam")
            return
        
        user_last_time[user_id] = now
        
        # Add to processing queue
        loop = asyncio.get_running_loop()
        queue_size = request_queue.qsize()
        await request_queue.put((message, loop))
        
        # Notify user of queue position if there's a queue
        if queue_size > 0:
            await notify_queue_position(message, queue_size + 1)
        
        logger.debug(f"Message from {user_id} added to queue (position: {queue_size + 1})")
    except Exception as e:
        logger.error(f"Error in handle_message: {e}")


# ============================================================================
# Application Startup and Shutdown
# ============================================================================

async def on_startup() -> None:
    """Initialize bot on startup."""
    try:
        # Start queue processor
        asyncio.create_task(queue_processor())
        
        # Initialize statistics
        global stats
        stats["last_restart"] = int(time.time())
        save_stats(stats)
        
        logger.info("✅ Bot started successfully")
        logger.info(f"🤖 Model: {POLLINATIONS_MODEL} (Pollinations.ai)")
        logger.info(f"📁 Dataset: {DATASET_FILE}")
    except Exception as e:
        logger.error(f"Error during bot startup: {e}")
        raise


async def main() -> None:
    """Main bot entry point."""
    try:
        # Register startup handler
        dp.startup.register(on_startup)
        
        # Start polling
        logger.info("Starting polling...")
        await dp.start_polling(bot)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error in main: {e}")
        raise
    finally:
        try:
            await bot.session.close()
            logger.info("Bot session closed")
        except Exception as e:
            logger.error(f"Error closing bot session: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
