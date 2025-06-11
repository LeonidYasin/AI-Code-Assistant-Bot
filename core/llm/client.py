from typing import Optional, Dict, Any, List, Union
from langchain_core.language_models import BaseLLM
from config import settings
import logging
import json

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self):
        self._model: Optional[BaseLLM] = None
        self._initialized = False
    
    def initialize(self, use_gigachat: bool = True):
        """Initialize the LLM client with the specified provider"""
        if self._initialized:
            return
            
        try:
            if use_gigachat:
                from .gigachat import GigaChatWrapper
                if not settings.GIGACHAT_CREDS:
                    raise ValueError("Gigachat credentials not found in settings")
                self._model = GigaChatWrapper(settings.GIGACHAT_CREDS)
                logger.info("Initialized with Gigachat provider")
            else:
                from .bothub import BotHubWrapper
                if not settings.BOT_HUB_API_KEY:
                    raise ValueError("BotHub API key not found in settings")
                self._model = BotHubWrapper(settings.BOT_HUB_API_KEY)
                logger.info("Initialized with BotHub provider")
                
            self._initialized = True
            
        except ImportError as e:
            logger.error(f"Failed to import LLM provider: {e}")
            raise
        except Exception as e:
            logger.error(f"LLM initialization error: {e}")
            raise
    
    def call(self, prompt: str, context: str = "", **kwargs) -> str:
        """
        Call the LLM with the given prompt and optional context
        
        Args:
            prompt: The main prompt text
            context: Additional context for the prompt
            **kwargs: Additional arguments for the LLM
            
        Returns:
            Generated text response
        """
        if not self._initialized:
            self.initialize(use_gigachat=True)
            
        if not self._model:
            logger.error("LLM model not available")
            return "Ошибка: Модель ИИ не инициализирована. Пожалуйста, проверьте настройки."
        
        try:
            # For project management, we might need to handle different types of prompts
            if kwargs.get('is_json', False):
                # For JSON responses, we need to guide the model
                full_prompt = (
                    f"Ты - AI Code Assistant. Ответь в формате JSON. "
                    f"Контекст: {context}\n\n"
                    f"Запрос: {prompt}\n\n"
                    "Ответ должен быть только в формате JSON, без дополнительного текста."
                )
            else:
                # For regular text responses
                full_prompt = f"Контекст:\n{context}\n\nЗапрос: {prompt}"
            
            logger.debug(f"Sending prompt to LLM: {full_prompt[:200]}...")
            result = self._model.generate([full_prompt])
            
            if not result.generations or not result.generations[0]:
                raise ValueError("Empty response from LLM")
                
            response = result.generations[0][0].text
            logger.debug(f"Received response from LLM: {response[:200]}...")
            
            # Clean up the response if it's a JSON string
            if kwargs.get('is_json', False):
                try:
                    # Try to parse and re-serialize to ensure valid JSON
                    parsed = json.loads(response)
                    response = json.dumps(parsed, ensure_ascii=False, indent=2)
                except json.JSONDecodeError:
                    logger.warning("Failed to parse LLM response as JSON")
            
            return response
            
        except Exception as e:
            logger.error(f"LLM call error: {e}", exc_info=True)
            return (
                "Извините, произошла ошибка при обработке вашего запроса. "
                "Пожалуйста, попробуйте снова или уточните ваш запрос."
            )

# Global instance
llm_client = LLMClient()

# Initialize with Gigachat by default
try:
    llm_client.initialize(use_gigachat=True)
except Exception as e:
    logger.error(f"Failed to initialize LLM client: {e}")