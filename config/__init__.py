import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    def __init__(self):
        self.TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
        self.BOT_HUB_API_KEY = os.getenv("BOT_HUB_API_KEY")
        self.GIGACHAT_CREDS = {
            "model": "GigaChat-2-Max",
            "verify_ssl_certs": False,
            "credentials": os.getenv("GIGACHAT_CREDENTIALS")
        }
        self.PROJECT_DIR = "./my_project"
        self.ALLOWED_EXTENSIONS = {".py", ".json", ".yaml", ".md"}
        self.SAFE_COMMANDS = ["dir", "pip install", "python", "git"]
        self.MAX_CONTEXT_LENGTH = 50000

config = Config()