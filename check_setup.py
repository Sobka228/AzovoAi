#!/usr/bin/env python3
"""Quick setup validation for AzovoAI bot"""

import os
import sys
import json

print("🔍 AzovoAI Setup Validation")
print("=" * 50)

# Check 1: .env file
print("\n[1] Environment Configuration")
if os.path.exists(".env"):
    print("   ✅ .env file exists")
    with open(".env", "r") as f:
        env_content = f.read()
        if "BOT_TOKEN" in env_content:
            print("   ✅ BOT_TOKEN is defined")
        else:
            print("   ❌ BOT_TOKEN not found in .env")
else:
    print("   ❌ .env file not found. Copy from .env.example and add BOT_TOKEN")

# Check 2: Requirements
print("\n[2] Dependencies")
try:
    import aiogram
    print(f"   ✅ aiogram {aiogram.__version__}")
except ImportError:
    print("   ⚠️  aiogram not installed. Run: pip install -r requirements.txt")

try:
    import requests
    print(f"   ✅ requests {requests.__version__}")
except ImportError:
    print("   ⚠️  requests not installed")

try:
    import dotenv
    print("   ✅ python-dotenv")
except ImportError:
    print("   ⚠️  python-dotenv not installed")

# Check 3: Data files
print("\n[3] Data Files")
data_files = ["dataset.txt", "bot_stats.json", "blacklist.json", "user_consent.json"]
for fname in data_files:
    if os.path.exists(fname):
        size = os.path.getsize(fname)
        print(f"   ✅ {fname} ({size} bytes)")
    else:
        print(f"   ℹ️  {fname} - will be created on first run")

# Check 4: Main code
print("\n[4] Code Check")
with open("main.py", "r") as f:
    code = f.read()
    
checks = [
    ("Pollinations.ai", "POLLINATIONS_URL" in code),
    ("ask_ai function", "def ask_ai" in code),
    ("No Ollama", "ask_ollama" not in code),
    ("Bot token check", "BOT_TOKEN" in code),
]

for check_name, result in checks:
    status = "✅" if result else "❌"
    print(f"   {status} {check_name}")

# Check 5: Requirements file
print("\n[5] Requirements File")
with open("requirements.txt", "r") as f:
    reqs = f.read()
    
required = {
    "aiogram": "aiogram" in reqs,
    "requests": "requests" in reqs,
    "python-dotenv": "python-dotenv" in reqs or "python_dotenv" in reqs,
}

for pkg, found in required.items():
    status = "✅" if found else "❌"
    print(f"   {status} {pkg}")

print("\n" + "=" * 50)
print("\n✨ Setup Overview:")
print("   Root: main.py (updated to use Pollinations.ai)")
print("   API: https://text.pollinations.ai/")
print("   Model: openai (free, no auth needed)")
print("   Framework: aiogram 3.4.1")
print("\n📝 Next Steps:")
print("   1. Edit .env and add your BOT_TOKEN from @BotFather")
print("   2. Run: python main.py")
print("   3. Test /ping command in your bot")
print("\n")
