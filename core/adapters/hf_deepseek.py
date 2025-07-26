import os
import httpx
from typing import List, Dict

class HFDeepSeekAdapter:
    def __init__(self, model: str = None):
        self.token = os.getenv("HF_TOKEN")
        self.model = model or os.getenv("HF_MODEL", "deepseek-ai/DeepSeek-Coder-V2-Instruct")

    async def ask(self, messages: List[Dict[str, str]]) -> str:
        url = "https://router.huggingface.co/v1/chat/completions"
        headers = {"Authorization": f"Bearer {self.token}"}
        payload = {"model": self.model, "messages": messages, "max_tokens": 1024, "temperature": 0.3}
        async with httpx.AsyncClient(timeout=120) as client:
            r = await client.post(url, headers=headers, json=payload)
            r.raise_for_status()
            return r.json()["choices"][0]["message"]["content"]