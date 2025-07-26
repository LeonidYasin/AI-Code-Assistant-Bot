# C:\Bot\core\ai\ai_router.py
import os
import yaml
from typing import List, Dict

PROVIDER = os.getenv("PROVIDER", "hf_deepseek")

with open("config/models.yaml", encoding="utf-8") as f:
    cfg = yaml.safe_load(f)
adapter_cfg = cfg["providers"][PROVIDER]

# импорт из core.adapters
module_name, class_name = adapter_cfg["class"].rsplit(".", 1)
mod = __import__(f"core.{module_name}", fromlist=[class_name])
adapter = getattr(mod, class_name)()

async def ask(messages: List[Dict[str, str]]) -> str:
    return await adapter.ask(messages)





