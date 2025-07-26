import os
import yaml
from typing import List, Dict

# Загружаем переменные окружения из .env файла
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # Fallback: простая загрузка .env
    def load_simple_env():
        if os.path.exists(".env"):
            with open(".env", 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        os.environ[key.strip()] = value.strip().strip('"').strip("'")
    load_simple_env()

PROVIDER = os.getenv("PROVIDER", "hf_deepseek")

# Загружаем маппинг
try:
    with open("config/models.yaml", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    
    if PROVIDER not in cfg["providers"]:
        raise ValueError(f"Provider {PROVIDER} not found in config")
        
    adapter_cfg = cfg["providers"][PROVIDER]

    # Динамический импорт
    module_name, class_name = adapter_cfg["class"].rsplit(".", 1)
    # Преобразуем путь adapters.* в core.adapters.*
    if module_name.startswith("adapters."):
        module_name = "core." + module_name
    
    print(f"Initializing AI adapter: {PROVIDER} ({class_name})")
    mod = __import__(module_name, fromlist=[class_name])
    adapter = getattr(mod, class_name)()
    print(f"✅ AI adapter initialized successfully: {PROVIDER}")
except Exception as e:
    print(f"Warning: Could not initialize AI adapter: {e}")
    print(f"Provider: {PROVIDER}")
    print(f"Available env vars: HF_TOKEN={'set' if os.getenv('HF_TOKEN') else 'not set'}")
    adapter = None

async def ask(messages: List[Dict[str, str]]) -> str:
    """Ask a question to the AI model."""
    if adapter is None:
        return "Error: AI adapter not initialized"
    try:
        return await adapter.ask(messages)
    except Exception as e:
        return f"Error asking AI: {e}"