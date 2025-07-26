import os
from typing import List, Dict
from gigachat import GigaChat

class GigaChatAdapter:
    def __init__(self, model: str = None):
        self.model = model or "GigaChat-Pro"
        self.client = GigaChat(credentials=os.getenv("GIGACHAT_API_KEY"), verify_ssl_certs=False)

    async def ask(self, messages: List[Dict[str, str]]) -> str:
        return self.client.chat(messages=messages, model=self.model).choices[0].message.content