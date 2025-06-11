import os
from dataclasses import dataclass, field
from dotenv import load_dotenv



load_dotenv()

def get_gigachat_creds():
    """Get GigaChat credentials with default model configuration.
    
    Returns:
        dict: Configuration dictionary for GigaChat client
    """
    from .models import GIGACHAT_MODELS, DEFAULT_MODEL
    
    return {
        "credentials": os.getenv("GIGACHAT_CREDENTIALS"),
        "model": GIGACHAT_MODELS[DEFAULT_MODEL],  # Use the default model from config
        "verify_ssl": False,
        "timeout": 30,
        "profanity_check": False,
        "streaming": False
    }

@dataclass
class Settings:
    TELEGRAM_TOKEN: str = os.getenv("TELEGRAM_TOKEN")
    GIGACHAT_CREDS: dict = field(default_factory=get_gigachat_creds)
    BOT_HUB_API_KEY: str = os.getenv("BOT_HUB_API_KEY", "")  # Добавлено
    PROJECT_DIR: str = os.getenv("PROJECT_DIR", "./my_project")
    ALLOWED_EXTENSIONS: set = field(default_factory=lambda: {".py", ".json", ".yaml", ".md"})
    SAFE_COMMANDS: list = field(default_factory=lambda: ["python", "pip", "git"])
    MAX_CONTEXT_LENGTH: int = 50000

settings = Settings()  # Экспортируем settings вместо config