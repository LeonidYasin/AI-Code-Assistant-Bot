from typing import Optional, Dict, Any, List, Union
from langchain_core.language_models import BaseLLM
from config import settings
import logging
import json
import traceback
from .gigachat import PaymentRequiredError
from gigachat.exceptions import ResponseError

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self):
        self._model: Optional[BaseLLM] = None
        self._initialized = False
    
    def initialize(self, use_gigachat: bool = True):
        """Initialize the LLM client with the specified provider"""
        if self._initialized:
            logger.debug("LLM client already initialized, skipping initialization")
            return
            
        try:
            if use_gigachat:
                from .gigachat import GigaChatWrapper
                if not settings.GIGACHAT_CREDS:
                    error_msg = "Gigachat credentials not found in settings"
                    logger.error(error_msg)
                    raise ValueError(error_msg)
                    
                logger.info(f"Initializing GigaChat with config: { {k: '***' if k == 'credentials' else v for k, v in settings.GIGACHAT_CREDS.items()} }")
                self._model = GigaChatWrapper(settings.GIGACHAT_CREDS)
                
                # Log model information
                if hasattr(self._model, '_client'):
                    logger.info(f"GigaChat client created. Model: {getattr(self._model._client, 'model', 'unknown')}")
                    logger.debug(f"GigaChat client details: {self._model._client}")
                else:
                    logger.warning("GigaChat client created but _client attribute not found")
                    
            else:
                from .bothub import BotHubWrapper
                logger.info("Initializing BotHub provider")
                self._model = BotHubWrapper(settings.BOTHUB_CREDS)
                logger.info("Initialized with BotHub provider")
            
            self._initialized = True
            logger.info(f"LLM client initialization complete. Model type: {type(self._model).__name__}")
            
        except ImportError as e:
            logger.error(f"Failed to import LLM provider: {e}")
            raise
        except Exception as e:
            logger.error(f"LLM initialization error: {e}", exc_info=True)
            raise
    
    def _get_error_message(self, error: Exception) -> str:
        """Get a user-friendly error message based on the exception type."""
        # Log the full error for debugging
        error_type = type(error).__name__
        error_msg = str(error)
        
        # Common payment required errors
        if (isinstance(error, (PaymentRequiredError, ResponseError)) and 
            (not hasattr(error, 'status_code') or getattr(error, 'status_code', None) == 402)):
            
            # Extract model information if available
            model_info = f" (Модель: {getattr(error, 'model', 'неизвестна')})" if hasattr(error, 'model') else ""
            logger.info(f"Payment required error: {error_type} - {error_msg}{model_info}")
            
            return (
                f"🔴 *ОШИБКА: ТРЕБУЕТСЯ ОПЛАТА ПОДПИСКИ{model_info}*\n\n"
                "Для использования функций ИИ требуется активная подписка на GigaChat.\n\n"
                "*ЧТО НУЖНО СДЕЛАТЬ:*\n"
                "1. Перейдите на сайт GigaChat: https://developers.sber.ru/portal/login\n"
                "2. Войдите в свой аккаунт\n"
                "3. Проверьте статус подписки в личном кабинете\n"
                "4. При необходимости оформите или продлите подписку\n\n"
                "*ДОПОЛНИТЕЛЬНАЯ ИНФОРМАЦИЯ:*\n"
                "• Тарифы и условия: https://developers.sber.ru/portal/products/gigachat\n"
                "• Поддержка: https://developers.sber.ru/portal/support"
            )
            
        # Handle JSON decode errors
        elif isinstance(error, json.JSONDecodeError):
            logger.warning(f"JSON decode error: {error_msg}")
            return (
                "❌ Ошибка обработки ответа\n\n"
                "Не удалось обработать ответ от сервера. Пожалуйста, попробуйте снова."
            )
            
        # Handle timeouts
        elif isinstance(error, TimeoutError):
            logger.warning(f"Request timeout: {error_msg}")
            return (
                "⌛ Превышено время ожидания ответа\n\n"
                "Сервер не ответил вовремя. Пожалуйста, попробуйте снова через некоторое время."
            )
            
        # For all other errors, log them and show a generic message
        else:
            # Log the full error with traceback for debugging
            logger.error(f"Unexpected error: {error_type} - {error_msg}", exc_info=True)
            return (
                "❌ Произошла ошибка при обработке запроса\n\n"
                "Пожалуйста, попробуйте снова. Если ошибка повторяется, "
                "сообщите об этом в поддержку и укажите следующую информацию:\n"
                f"Тип ошибки: {error_type}"
            )
    
    def call(self, prompt: str, context: str = "", **kwargs) -> str:
        """
        Call the LLM with the given prompt and optional context
        
        Args:
            prompt: The main prompt text
            context: Additional context for the prompt
            **kwargs: Additional arguments for the LLM
                - is_json: If True, expects a JSON response
                - retry_count: Number of retry attempts (default: 1)
            
        Returns:
            Generated text response or error message
        """
        if not self._initialized:
            self.initialize(use_gigachat=True)
            
        if not self._model:
            logger.error("LLM model not available")
            return "❌ Ошибка: Модель ИИ не инициализирована. Пожалуйста, проверьте настройки."
        
        retry_count = kwargs.get('retry_count', 1)
        last_error = None
        
        for attempt in range(max(1, retry_count)):
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
                
                logger.debug(f"Sending prompt to LLM (attempt {attempt + 1}): {full_prompt[:200]}...")
                logger.debug(f"Prompt: {full_prompt[:200]}..." if len(str(full_prompt)) > 200 else f"Prompt: {full_prompt}")
                
                # Log model info if available
                if hasattr(self._model, '_client') and hasattr(self._model._client, 'model'):
                    logger.debug(f"Using model: {self._model._client.model}")
                
                # Generate the response
                result = self._model.generate([full_prompt])
                
                # Handle the response - extract text from the result
                try:
                    response = ""
                    
                    # First, try to get the raw response from the model
                    if hasattr(result, 'generations') and result.generations:
                        generations = result.generations
                        if generations and len(generations) > 0 and len(generations[0]) > 0:
                            generation = generations[0][0]
                            
                            # Handle different response formats
                            if hasattr(generation, 'text'):
                                response = generation.text
                            elif hasattr(generation, 'message'):
                                # Handle AIMessage object
                                message = generation.message
                                if hasattr(message, 'content'):
                                    response = message.content
                                elif hasattr(message, 'response_metadata') and 'content' in message.response_metadata:
                                    response = message.response_metadata['content']
                                else:
                                    response = str(message)
                            else:
                                response = str(generation)
                                    
                            # If the response is a string representation of an object, try to extract content
                            if response.startswith("content='") and "' additional_kwargs=" in response:
                                try:
                                    # Extract the content part
                                    content_start = response.find("content='") + len("content='")
                                    content_end = response.find("'", content_start)
                                    if content_end > content_start:
                                        response = response[content_start:content_end]
                                        # Unescape any escaped characters
                                        response = response.encode().decode('unicode_escape')
                                        # Extract JSON if present
                                        if '```json' in response:
                                            json_start = response.find('```json\n') + 7
                                            json_end = response.find('\n```', json_start)
                                            if json_end > json_start:
                                                response = response[json_start:json_end].strip()
                                except Exception as e:
                                    logger.warning(f"Error parsing response content: {e}")
                    
                    # If no response extracted yet, try to get it from the result directly
                    if not response and hasattr(result, 'content'):
                        response = result.content
                    
                    # If still no response, try to get it from the first choice
                    if not response and hasattr(result, 'choices') and len(result.choices) > 0:
                        choice = result.choices[0]
                        if hasattr(choice, 'message'):
                            message = choice.message
                            if hasattr(message, 'content'):
                                response = message.content
                            elif hasattr(message, 'response_metadata') and 'content' in message.response_metadata:
                                response = message.response_metadata['content']
                            else:
                                response = str(message)
                        elif hasattr(choice, 'text'):
                            response = choice.text
                    
                    # If still no response, convert to string
                    if not response:
                        response = str(result)
                    
                    # If the response is a string representation of an object, try to extract content
                    if isinstance(response, str) and response.startswith("content='") and "' additional_kwargs=" in response:
                        try:
                            # Extract the content part
                            content_start = response.find("content='") + len("content='")
                            content_end = response.find("'", content_start)
                            if content_end > content_start:
                                response = response[content_start:content_end]
                                # Unescape any escaped characters
                                response = response.encode().decode('unicode_escape')
                        except Exception as e:
                            logger.warning(f"Error parsing response content: {e}")
                    
                    # Extract JSON if present in the response
                    if isinstance(response, str) and '```json' in response:
                        try:
                            json_start = response.find('```json\n') + 7
                            json_end = response.find('\n```', json_start)
                            if json_end > json_start:
                                response = response[json_start:json_end].strip()
                        except Exception as e:
                            logger.warning(f"Error extracting JSON from response: {e}")
                        
                except Exception as e:
                    logger.error(f"Error processing response: {e}", exc_info=True)
                    response = str(result) if hasattr(result, '__str__') else "Error processing response"
                
                # Log the response
                response_str = str(response)
                logger.debug(f"Response received (type: {type(response)}): {response_str[:500]}..." 
                            if len(response_str) > 500 else f"Response: {response_str}")
                
                if kwargs.get('is_json', False):
                    try:
                        # Try to parse and re-serialize to ensure valid JSON
                        parsed = json.loads(response)
                        logger.debug("Successfully parsed JSON response")
                        return json.dumps(parsed, ensure_ascii=False, indent=2)
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse JSON response: {e}")
                        logger.debug(f"Response content that failed to parse: {response}")
                        if attempt == retry_count - 1:  # Last attempt
                            raise
                        continue
                
                return response
                
            except Exception as e:
                last_error = e
                logger.error(f"LLM call error (attempt {attempt + 1}): {e}")
                logger.debug(traceback.format_exc())
                
                # Don't retry for payment required errors
                if isinstance(e, PaymentRequiredError):
                    break
                
                if attempt < retry_count - 1:
                    logger.info(f"Retrying... (attempt {attempt + 2} of {retry_count})")
                    continue
        
        # If we get here, all attempts failed
        error_message = self._get_error_message(last_error)
        logger.error(f"LLM call failed after {retry_count} attempts. Last error: {last_error}")
        return error_message

# Global instance
llm_client = LLMClient()

# Initialize with Gigachat by default
try:
    llm_client.initialize(use_gigachat=True)
except Exception as e:
    logger.error(f"Failed to initialize LLM client: {e}")