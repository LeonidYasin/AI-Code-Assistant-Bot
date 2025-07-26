#!/bin/bash

# AI Code Assistant - Quick Start Script

echo "🤖 AI Code Assistant"
echo "===================="

# Проверяем аргументы
if [ $# -eq 0 ]; then
    echo "Использование:"
    echo "  ./run.sh help                    # Показать справку"
    echo "  ./run.sh project list           # Список проектов"
    echo "  ./run.sh file list              # Список файлов"
    echo "  ./run.sh bot                     # Запустить Telegram бота"
    echo ""
    echo "Или используйте напрямую:"
    echo "  python3 main.py --help"
    exit 0
fi

# Запуск команд
case "$1" in
    "help")
        python3 main.py --help
        ;;
    "bot")
        echo "🚀 Запуск Telegram бота..."
        if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
            echo "⚠️  Установите TELEGRAM_BOT_TOKEN в .env файле"
            echo "Пример: echo 'TELEGRAM_BOT_TOKEN=your_token_here' >> .env"
        fi
        python3 main.py
        ;;
    *)
        # Передаем все аргументы в main.py
        python3 main.py "$@"
        ;;
esac