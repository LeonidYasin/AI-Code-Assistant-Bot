from gigachat import GigaChat
from gigachat.models import Chat
import logging
from config import settings
from config.models import GIGACHAT_MODELS

class GigaChatClient:
    def __init__(self, model: str):
        self.model_name = GIGACHAT_MODELS.get(model, GIGACHAT_MODELS['latest'])
        self._client = None
        
    def initialize(self):
        try:
            self._client = GigaChat(
                model=self.model_name,
                **settings.GIGACHAT_CREDS
            )
            self._client.get_models()  # Проверка подключения
        except Exception as e:
            logging.error(f"GigaChat init failed: {e}")
            raise
    
    def call(self, prompt: str) -> str:
        try:
            response = self._client.chat(
                Chat(messages=[{"role": "user", "content": prompt}])
            )
            return response.choices[0].message.content
        except Exception as e:
            logging.error(f"GigaChat error: {e}")
            return f"Ошибка GigaChat: {str(e)}"