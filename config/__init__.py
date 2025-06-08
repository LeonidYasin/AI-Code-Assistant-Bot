import os
from dataclasses import dataclass, field
from dotenv import load_dotenv



load_dotenv()

def get_gigachat_creds():
    return {
        "credentials": os.getenv("GIGACHAT_CREDENTIALS"),
        "model": "GigaChat-2-Max",
        "verify_ssl": False
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