import os
from openai import OpenAI
from .base import BaseAdapter

class HFOpenAIAdapter(BaseAdapter):
    """Hugging Face via OpenAI-compatible router."""

    def __init__(self):
        self.client = OpenAI(
            base_url="https://router.huggingface.co/v1",
            api_key=os.getenv("HF_TOKEN"),
        )

    def ask(self, messages: list[dict[str, str]], **kwargs) -> str:
        resp = self.client.chat.completions.create(
            model=kwargs.get("model") or "deepseek-ai/deepseek-coder-6.7b-instruct",
            messages=messages,
            temperature=kwargs.get("temperature", 0.2),
            max_tokens=kwargs.get("max_tokens", 1024),
        )
        return resp.choices[0].message.content