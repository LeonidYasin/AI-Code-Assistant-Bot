from typing import Optional
from langchain_core.language_models import BaseChatModel
from config import config

class LLMClient:
    def __init__(self):
        self._model: Optional[BaseChatModel] = None
    
    def initialize(self, use_gigachat: bool):
        if use_gigachat:
            from .gigachat import GigaChatWrapper
            self._model = GigaChatWrapper(config.GIGACHAT_CREDS)
        else:
            from .bothub import BotHubWrapper
            self._model = BotHubWrapper(config.BOT_HUB_API_KEY)
    
    def call(self, prompt: str, context: str = "") -> str:
        full_prompt = f"Контекст:\n{context}\nЗадача: {prompt}"
        return self._model.invoke(full_prompt).content