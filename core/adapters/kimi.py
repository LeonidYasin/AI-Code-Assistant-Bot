import os
import httpx
from typing import List, Dict

class KimiAdapter:
    def __init__(self, model: str = None):
        self.api_key = os.getenv("KIMI_API_KEY")
        self.model = model or "moonshot-v1-8k"

    async def ask(self, messages: List[Dict[str, str]]) -> str:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        payload = {"model": self.model, "messages": messages, "max_tokens": 1024, "temperature": 0.3}
        async with httpx.AsyncClient(timeout=60) as client:
            r = await client.post("https://api.moonshot.cn/v1/chat/completions",
                                  headers=headers, json=payload)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]