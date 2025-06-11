from typing import Any, Dict, Optional
from telegram import Update
from telegram.ext import ContextTypes
import logging

logger = logging.getLogger(__name__)

def extract_command_args(update: Update, context: ContextTypes.DEFAULT_TYPE) -> tuple[str, list]:
    """Extract command and arguments from update"""
    message = update.message.text
    if not message.startswith('/'):
        return message.lower().split(' ', 1)[0], message.split(' ')[1:]
    
    # Handle commands with @bot_username
    parts = message.split('@', 1)
    command = parts[0].split(' ', 1)
    cmd = command[0].lstrip('/')
    args = command[1].split() if len(command) > 1 else []
    
    return cmd, args

def format_error(error: Exception) -> str:
    """Format error message for user"""
    error_message = str(error)
    if not error_message:
        return "❌ Произошла неизвестная ошибка"
    return f"❌ {error_message}"

def format_success(message: str) -> str:
    """Format success message"""
    return f"✅ {message}"

def format_info(message: str) -> str:
    """Format info message"""
    return f"ℹ️ {message}"

def get_chat_id(update: Update) -> int:
    """Get chat ID from update"""
    return update.effective_chat.id if update.effective_chat else 0
