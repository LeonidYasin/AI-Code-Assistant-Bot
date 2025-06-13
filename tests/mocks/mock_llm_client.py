"""
Mock LLM client for testing.
"""
from typing import Dict, Any, Optional, List, Union, AsyncGenerator, Type, TypeVar, Callable
import json
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from dataclasses import dataclass

# Type variable for the generic client
T = TypeVar('T', bound='MockLLMClient')

class LazyLLMClient:
    """Mock implementation of LazyLLMClient to match the real one."""
    _instance = None
    _initialized = False
    
    def __init__(self):
        if LazyLLMClient._instance is not None:
            raise RuntimeError("Use get_instance() instead")
        self._client = None
        self._initialized = False
    
    @classmethod
    def get_instance(cls) -> 'LazyLLMClient':
        """Get or create the singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def _ensure_initialized(self):
        """Ensure the client is initialized."""
        if not self._initialized or self._client is None:
            self._client = MockLLMClient()
            self._initialized = True
            print(f"[DEBUG] Initialized mock LLM client: {self._client}")
        return self._client
    
    def __getattr__(self, name):
        """Delegate attribute access to the underlying client."""
        self._ensure_initialized()
        return getattr(self._client, name)

@dataclass
class MockResponse:
    """Mock response object that mimics LLM response."""
    content: Any
    model: str = "mock-model"
    usage: Dict[str, int] = None
    
    def __init__(self, content, **kwargs):
        self.content = content
        self.model = kwargs.get('model', 'mock-model')
        self.usage = kwargs.get('usage', {
            'prompt_tokens': 10,
            'completion_tokens': 20,
            'total_tokens': 30
        })
    
    def __str__(self):
        return json.dumps(self.content) if isinstance(self.content, (dict, list)) else str(self.content)
    
    def dict(self):
        """Convert to dict for JSON serialization."""
        return {
            'content': self.content,
            'model': self.model,
            'usage': self.usage
        }
        
    def to_dict(self):
        """Alias for dict() for compatibility."""
        return self.dict()
        
    def __getitem__(self, key):
        """Allow dictionary-style access for compatibility."""
        return getattr(self, key)

class MockLLMClient:
    """Mock LLM client for testing."""
    
    def __init__(self):
        self._model = None
        self._initialized = False
        self._client = self  # For compatibility with the real client
        self.model = "mock-model"
        
        # Set up responses for different command types
        self.responses = {
            "create_project": {
                "type": "create_project",
                "params": {"name": "test_project"},
                "confidence": 0.9,
                "explanation": "Creating a new project"
            },
            "switch_project": {
                "type": "switch_project",
                "params": {"name": "test_project"},
                "confidence": 0.9,
                "explanation": "Switching to project"
            },
            "create_file": {
                "type": "create_file",
                "params": {"path": "main.py", "content": "print('Hello')"},
                "confidence": 0.9,
                "explanation": "Creating a new file"
            },
            "list_projects": {
                "type": "list_projects",
                "params": {},
                "confidence": 0.95,
                "explanation": "Listing all projects"
            }
        }
        
        # Initialize with default values
        self.initialize()
    
    def initialize(self, *args, **kwargs):
        """Mock initialization."""
        self._initialized = True
        return self
        
    async def call(self, prompt: str, **kwargs) -> str:
        """Mock call method that simulates LLM response."""
        print(f"[MOCK_LLM] Received prompt: {prompt[:200]}...")
        response = await self._get_mock_response(prompt)
        print(f"[MOCK_LLM] Sending response: {str(response)[:200]}...")
        return str(response)
        
    # Define aliases for backward compatibility
    call_async = call  # Alias for backward compatibility
    ainvoke = call    # Alias for LangChain compatibility
    invoke = call     # Alias for LangChain compatibility
        
    async def _invoke(self, prompt: str, **kwargs) -> MockResponse:
        """Mock invoke method that simulates LLM response."""
        return await self._get_mock_response(prompt)
    
    async def _ainvoke(self, prompt: str, **kwargs) -> MockResponse:
        """Async version of invoke."""
        return await self._invoke(prompt, **kwargs)
    
    async def _call_async(self, prompt: str, is_json: bool = False, **kwargs) -> Union[str, Dict[str, Any]]:
        """Legacy async call method for backward compatibility."""
        response = await self._invoke(prompt, **kwargs)
        if is_json:
            return response.content if hasattr(response, 'content') else response
        return str(response)
    
    def initialize(self, *args, **kwargs):
        """Mock initialization."""
        self._initialized = True
        return self
    
    async def _invoke(self, prompt: str, **kwargs) -> MockResponse:
        """Mock invoke method that simulates LLM response."""
        await asyncio.sleep(0.1)  # Simulate async delay
        response = await self._get_mock_response(prompt)
        # Return the content directly as the response
        return response
    
    async def _ainvoke(self, prompt: str, **kwargs) -> MockResponse:
        """Async version of invoke."""
        return await self._invoke(prompt, **kwargs)
    
    async def _call_async(self, prompt: str, is_json: bool = False, **kwargs) -> Union[str, Dict[str, Any]]:
        """Legacy async call method for backward compatibility."""
        response = await self._invoke(prompt, **kwargs)
        if is_json:
            return response.content if hasattr(response, 'content') else response
        return str(response)
    
    async def _get_mock_response(self, prompt: str) -> MockResponse:
        """Get a mock response based on the prompt."""
        # Check for specific commands in the prompt
        if any(phrase in prompt.lower() for phrase in ["создай проект", "create project"]):
            response = self.responses["create_project"]
        elif any(phrase in prompt.lower() for phrase in ["активируй проект", "switch to project"]):
            response = self.responses["switch_project"]
        elif any(phrase in prompt.lower() for phrase in ["создай файл", "create file"]):
            response = self.responses["create_file"]
        elif any(phrase in prompt.lower() for phrase in ["покажи список проектов", "list projects"]):
            response = self.responses["list_projects"]
            
        # Default to list_projects for any other input
        else:
            response = self.responses["list_projects"]
        
        # Format the response as a JSON string that matches what the response parser expects
        response_json = json.dumps({
            "type": response["type"],
            "params": response["params"],
            "confidence": response["confidence"],
            "explanation": response["explanation"]
        }, ensure_ascii=False)
        
        # Return the response as a string that can be parsed by the response parser
        # The response parser looks for JSON in markdown code blocks, so we'll format it that way
        return MockResponse(f"""```json
{response_json}
```""")
    
    def __getattr__(self, name):
        """Delegate all other attributes to a mock object."""
        if name.startswith('__') and name.endswith('__'):
            # Handle special methods
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
        
        # Return a mock for any other attribute
        mock = MagicMock()
        setattr(self, name, mock)
        return mock
