import os
import yaml
from typing import List, Dict

PROVIDER = os.getenv("PROVIDER", "hf_deepseek")

# Загружаем маппинг
try:
    with open("config/models.yaml", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    adapter_cfg = cfg["providers"][PROVIDER]

    # Динамический импорт
    module_name, class_name = adapter_cfg["class"].rsplit(".", 1)
    # Преобразуем путь adapters.* в core.adapters.*
    if module_name.startswith("adapters."):
        module_name = "core." + module_name
    mod = __import__(module_name, fromlist=[class_name])
    adapter = getattr(mod, class_name)()
except Exception as e:
    print(f"Warning: Could not initialize AI adapter: {e}")
    adapter = None

async def ask(messages: List[Dict[str, str]]) -> str:
    """Ask a question to the AI model."""
    if adapter is None:
        return "Error: AI adapter not initialized"
    try:
        return await adapter.ask(messages)
    except Exception as e:
        return f"Error asking AI: {e}"