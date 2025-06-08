import os
import logging
from config import settings

def analyze_project() -> str:
    context = ""
    try:
        for root, _, files in os.walk(settings.PROJECT_DIR):
            if "venv" in root or "__pycache__" in root:
                continue
            for file in files:
                if os.path.splitext(file)[1] in settings.ALLOWED_EXTENSIONS:
                    try:
                        with open(os.path.join(root, file), "r", encoding="utf-8") as f:
                            context += f"File: {file}\n{f.read()}\n\n"
                    except UnicodeDecodeError:
                        continue
        
        return context[:settings.MAX_CONTEXT_LENGTH]
    except Exception as e:
        logging.error(f"Project analysis error: {e}")
        return ""