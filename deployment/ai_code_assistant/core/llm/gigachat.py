from langchain_gigachat import GigaChat
from langchain_core.language_models import BaseLLM
from langchain_core.outputs import LLMResult
from typing import List, Optional, Dict, Any, Union
from config import settings
import logging
import json
import traceback
from gigachat.exceptions import ResponseError

logger = logging.getLogger(__name__)

class PaymentRequiredError(Exception):
    """Raised when the GigaChat API returns a payment required error."""
    def __init__(self, message: str, model: str = "unknown", original_error: Optional[Exception] = None):
        self.message = message
        self.model = model
        self.original_error = original_error
        full_message = f"{message} (Model: {model})"
        super().__init__(full_message)

class GigaChatWrapper(BaseLLM):
    """Правильная реализация обертки для GigaChat"""
    
    _client: Any  # Объявляем поле для клиента
    model: str = "GigaChat-Lite"  # Модель по умолчанию
    
    class Config:
        arbitrary_types_allowed = True  # Разрешаем произвольные типы для _client
    
    def __init__(self, credentials: dict):
        super().__init__()
        # Get model from credentials with fallback to GigaChat-Lite
        self.model = credentials.get("model", "GigaChat-Lite")
        print(f"\n[GigaChat] 🔍 INITIALIZING WITH MODEL: {self.model}")
        print(f"[GigaChat] 📋 Credentials keys: {list(credentials.keys())}")
        
        # Log non-sensitive credentials info
        creds_info = {k: '***' if k == 'credentials' else v 
                     for k, v in credentials.items() 
                     if k != 'credentials'}
        print(f"[GigaChat] ⚙️  Config: {creds_info}")
        
        try:
            print(f"[GigaChat] 🚀 Creating GigaChat client...")
            self._client = GigaChat(
                credentials=credentials.get("credentials"),
                model=self.model,  # Use the model from config
                verify_ssl_certs=credentials.get("verify_ssl", False),
                timeout=credentials.get("timeout", 30),
                profanity_check=credentials.get("profanity_check", False),
                streaming=credentials.get("streaming", False)
            )
            
            # Force set the model to ensure it's used
            if hasattr(self._client, 'model'):
                self._client.model = self.model
            
            # Log successful initialization with model info
            actual_model = getattr(self._client, 'model', 'unknown')
            print(f"[GigaChat] ✅ Successfully initialized with model: {actual_model}")
            print(f"[GigaChat] 🔗 Client class: {self._client.__class__.__name__}")
            
            # Log available models if possible
            if hasattr(self._client, 'get_models'):
                try:
                    print("[GigaChat] 🔄 Fetching available models...")
                    models = self._client.get_models()
                    if hasattr(models, 'data') and models.data:
                        print("[GigaChat] 📊 Available models:")
                        for m in models.data:
                            print(f"  - {getattr(m, 'id', 'unknown')} "
                                  f"(owned_by: {getattr(m, 'owned_by', 'N/A')})")
                    else:
                        print(f"[GigaChat] ℹ️  No models data available in response: {models}")
                except Exception as e:
                    print(f"[GigaChat] ⚠️  Could not fetch available models: {e}")
            else:
                print("[GigaChat] ℹ️  Client does not have get_models() method")
                    
        except Exception as e:
            logger.error(f"[GigaChat] Failed to initialize client: {e}", exc_info=True)
            raise
    
    def _generate(
        self,
        prompts: List[str],
        stop: Optional[List[str]] = None,
        **kwargs
    ) -> LLMResult:
        try:
            prompt = prompts[0] if prompts else ""
            model_name = getattr(self._client, 'model', 'unknown')
            
            # Prepare request data for logging
            request_data = {
                "model": model_name,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": kwargs.get("temperature", 0.7),
                "max_tokens": kwargs.get("max_tokens", 2000),
                "stop": stop,
                **{k: v for k, v in kwargs.items() if k not in ["temperature", "max_tokens"]}
            }
            
            # Log the full request
            logger.info("\n[GigaChat] Sending request to model: {}".format(model_name))
            logger.info("Request details:\n{}".format(json.dumps(request_data, indent=2, ensure_ascii=False)))
            
            try:
                # Make the API call
                response = self._client.invoke(prompt, **kwargs)
                
                # Extract model and usage information
                model_info = getattr(response, 'model', 'unknown')
                usage_info = getattr(response, 'usage', {})
                
                # Log token usage
                if hasattr(response, 'usage'):
                    usage_info = {
                        'prompt_tokens': getattr(response.usage, 'prompt_tokens', 0),
                        'completion_tokens': getattr(response.usage, 'completion_tokens', 0),
                        'total_tokens': getattr(response.usage, 'total_tokens', 0),
                        'precached_prompt_tokens': getattr(response.usage, 'precached_prompt_tokens', 0)
                    }
                    
                    logger.info(f"\n[GigaChat] Token usage for model {model_info}:")
                    logger.info(f"  Prompt tokens: {usage_info.get('prompt_tokens', 0)}")
                    logger.info(f"  Completion tokens: {usage_info.get('completion_tokens', 0)}")
                    logger.info(f"  Total tokens: {usage_info.get('total_tokens', 0)}")
                    if usage_info.get('precached_prompt_tokens', 0) > 0:
                        logger.info(f"  Precached prompt tokens: {usage_info.get('precached_prompt_tokens', 0)}")
                
                # Extract the response content
                response_content = str(response)
                
                # Format response for logging
                response_info = {
                    "model": model_info,
                    "object": "chat.completion",
                    "created": getattr(response, 'created', None),
                    "usage": usage_info,
                    "choices": [{
                        "message": {
                            "role": "assistant",
                            "content": response_content
                        },
                        "finish_reason": "stop",
                        "index": 0
                    }]
                }
                
                logger.info("\n[GigaChat] Received response:")
                logger.info(json.dumps(response_info, indent=2, ensure_ascii=False))
                
                # Create a proper LLMResult with token usage information
                return LLMResult(
                    generations=[[{
                        "text": response_content,
                        "message": response,
                        "model": model_info,
                        "usage": usage_info
                    }]],
                    llm_output={
                        "model": model_info,
                        "usage": usage_info
                    }
                )
                
            except ResponseError as e:
                error_info = {
                    "error": {
                        "type": type(e).__name__,
                        "status_code": getattr(e, 'status_code', 'N/A'),
                        "message": str(e),
                        "model": model_name
                    }
                }
                logger.error("\n[GigaChat] API Error:")
                logger.error(json.dumps(error_info, indent=2, ensure_ascii=False))
                
                if hasattr(e, 'status_code') and e.status_code == 402:
                    logger.info(f"Payment required for model: {model_name}")
                    raise PaymentRequiredError(
                        f"Payment required for GigaChat API. Model: {model_name}",
                        original_error=e
                    ) from e
                raise
                
            except Exception as e:
                error_info = {
                    "error": {
                        "type": type(e).__name__,
                        "message": str(e),
                        "model": model_name
                    }
                }
                logger.error("\n[GigaChat] Unexpected Error:")
                logger.error(json.dumps(error_info, indent=2, ensure_ascii=False))
                raise
            
        except ResponseError as e:
            if hasattr(e, 'status_code') and e.status_code == 402:
                error_msg = "Payment required for GigaChat API. Please check your subscription status."
                logger.error(error_msg)
                raise PaymentRequiredError(
                    "Для использования GigaChat требуется подписка. "
                    "Пожалуйста, проверьте статус вашей подписки на GigaChat.",
                    original_error=e
                ) from e
            logger.error(f"GigaChat API error: {e}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Unexpected error in GigaChat: {e}", exc_info=True)
            raise
    
    def _llm_type(self) -> str:
        return "gigachat"
    
    @property
    def client(self) -> Any:
        return self._client