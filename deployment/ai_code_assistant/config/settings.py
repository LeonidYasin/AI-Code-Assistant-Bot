"""Конфигурация приложения"""

# Безопасные команды, которые можно выполнять через бота
SAFE_COMMANDS = [
    'ls', 'dir', 'pwd', 'echo', 'cat', 'type',
    'git status', 'git log', 'git diff',
    'python --version', 'pip list'
]

# Настройки для Gigachat (если используется)
import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

from config.models import GIGACHAT_MODELS, DEFAULT_MODEL

GIGACHAT_CREDS = {
    "credentials": os.getenv("GIGACHAT_CREDENTIALS"),
    "model": GIGACHAT_MODELS[DEFAULT_MODEL],  # Using the default model from models.py
    "verify_ssl": False,
    "timeout": 30,
    "profanity_check": False,
    "streaming": False
}

# Log the model being used
print(f"[CONFIG] Using GigaChat model: {GIGACHAT_MODELS[DEFAULT_MODEL]} (key: {DEFAULT_MODEL})")

# Настройки логирования
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
            'level': 'INFO',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'bot.log',
            'maxBytes': 5 * 1024 * 1024,  # 5 MB
            'backupCount': 3,
            'formatter': 'standard',
            'encoding': 'utf-8',
        },
    },
    'loggers': {
        '': {  # root logger
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True
        },
    }
}
