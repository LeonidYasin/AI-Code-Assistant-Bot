from langchain_gigachat import GigaChat
from langchain_core.language_models import BaseLLM
from langchain_core.outputs import LLMResult
from typing import List, Optional, Dict, Any
from config import settings
import logging

logger = logging.getLogger(__name__)

class GigaChatWrapper(BaseLLM):
    """Правильная реализация обертки для GigaChat"""
    
    _client: Any  # Объявляем поле для клиента
    
    def __init__(self, credentials: dict):
        super().__init__()
        self._client = GigaChat(
            credentials=credentials["credentials"],
            model=credentials.get("model", "GigaChat-2-Max"),
            verify_ssl_certs=credentials.get("verify_ssl", False),
            timeout=30
        )
    
    def _generate(
        self,
        prompts: List[str],
        stop: Optional[List[str]] = None,
        **kwargs
    ) -> LLMResult:
        try:
            # Get the response from GigaChat
            response = self._client.invoke(prompts[0])
            
            # Extract the content from AIMessage if needed
            if hasattr(response, 'content'):
                response_text = response.content
            elif isinstance(response, str):
                response_text = response
            else:
                response_text = str(response)
                
            return LLMResult(
                generations=[[{"text": response_text, "message": response}]]
            )
        except Exception as e:
            logger.error(f"GigaChat error: {e}", exc_info=True)
            raise
    
    def _llm_type(self) -> str:
        return "gigachat"
    
    @property
    def client(self) -> Any:
        return self._client