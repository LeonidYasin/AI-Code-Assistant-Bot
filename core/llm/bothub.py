import requests
import logging
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class BotHubResponse:
    content: str
    status_code: int

class BotHubWrapper:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://bothub.chat/api/v2/openai/v1/chat/completions"
        self.timeout = 30

    def call(self, prompt: str) -> str:
        try:
            response = requests.post(
                self.base_url,
                json={
                    "model": "claude-3-7-sonnet",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 1000
                },
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"]
        
        except requests.exceptions.RequestException as e:
            logger.error(f"BotHub API error: {e}")
            return f"BotHub API недоступен: {str(e)}"