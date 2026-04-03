@echo off
REM script for azovoai

echo.
echo ================================
echo привет друк, активация бота АзovoAI погоди
echo ================================
echo   ,---.                                 ,---.  ,--. 
echo  /  O  \ ,-----. ,---.,--.  ,--.,---.  /  O  \ `--' 
echo |  .-.  |`-.  / | .-. |\  `'  /| .-. ||  .-.  |,--. 
echo |  | |  | /  `-.' '-' ' \    / ' '-' '|  | |  ||  | 
echo `--' `--'`-----' `---'   `--'   `---' `--' `--'`--' 
echo by @SOBKA_SUS / @SOBKA_TV_off

REM Check if .env exists
if not exist ".env" (
    echo.
    echo ERROR: .env file not found!
    echo.
    echo Please create .env file by copying .env.example:
    echo   copy .env.example .env
    echo.
    echo Then edit .env and add your BOT_TOKEN from @BotFather on Telegram
    echo.
    pause
    exit /b 1
)

REM Check if BOT_TOKEN is set
findstr /M "BOT_TOKEN" .env >nul
if errorlevel 1 (
    echo ERROR: BOT_TOKEN not found in .env
    echo.
    echo Edit .env and add your Telegram bot token
    pause
    exit /b 1
)

REM Install dependencies if needed
echo Checking dependencies...
python -m pip install -q -r requirements.txt

REM Run validation
echo Running setup validation...
python check_setup.py

REM Start the bot
echo.
echo Starting bot...
echo.
python main.py

if errorlevel 1 (
    echo.
    echo Bot crashed! Check the error above
    pause
)
