from typing import Optional
from langchain_core.language_models import BaseLLM
from config import settings
import logging

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self):
        self._model: Optional[BaseLLM] = None
    
    def initialize(self, use_gigachat: bool):
        try:
            if use_gigachat:
                from .gigachat import GigaChatWrapper
                self._model = GigaChatWrapper(settings.GIGACHAT_CREDS)
            else:
                from .bothub import BotHubWrapper
                self._model = BotHubWrapper(settings.BOT_HUB_API_KEY)
        except Exception as e:
            logger.error(f"LLM init error: {e}")
            raise
    
    def call(self, prompt: str, context: str = "") -> str:
        if not self._model:
            raise ValueError("LLM not initialized")
        
        try:
            full_prompt = f"Контекст:\n{context}\nЗадача: {prompt}"
            result = self._model.generate([full_prompt])
            return result.generations[0][0].text
        except Exception as e:
            logger.error(f"LLM call error: {e}")
            return f"Ошибка: {str(e)}"

llm_client = LLMClient()