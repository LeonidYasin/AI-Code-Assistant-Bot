import os
import yaml
from typing import List, Dict

PROVIDER = os.getenv("PROVIDER", "hf_deepseek")

# Загружаем маппинг
with open("config/models.yaml", encoding="utf-8") as f:
    cfg = yaml.safe_load(f)
adapter_cfg = cfg["providers"][PROVIDER]

# Динамический импорт
module_name, class_name = adapter_cfg["class"].rsplit(".", 1)
mod = __import__(module_name, fromlist=[class_name])
adapter = getattr(mod, class_name)()

async def ask(messages: List[Dict[str, str]]) -> str:
    return await adapter.ask(messages)