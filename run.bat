@echo off
REM AI Code Assistant - Windows Batch Script

echo 🤖 AI Code Assistant
echo ====================

if "%1"=="" (
    echo Использование:
    echo   run.bat help                    # Показать справку
    echo   run.bat project list           # Список проектов
    echo   run.bat file list              # Список файлов
    echo   run.bat chat                    # AI чат ассистент
    echo   run.bat analyze main.py        # Анализ файла с AI
    echo   run.bat bot                     # Запустить Telegram бота
    echo.
    echo Или используйте напрямую:
    echo   python main.py --help
    goto :EOF
)

if "%1"=="help" (
    python main.py --help
    goto :EOF
)

if "%1"=="bot" (
    echo 🚀 Запуск Telegram бота...
    if not defined TELEGRAM_BOT_TOKEN (
        echo ⚠️  Установите TELEGRAM_BOT_TOKEN в .env файле
        echo Пример: echo TELEGRAM_BOT_TOKEN=your_token_here >> .env
    )
    python main.py
    goto :EOF
)

if "%1"=="chat" (
    python ai_chat.py %2 %3 %4 %5
    goto :EOF
)

REM Передаем все аргументы в main.py
python main.py %*