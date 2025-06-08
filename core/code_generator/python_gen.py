from dataclasses import dataclass
from typing import Tuple  # Добавьте этот импорт
from core.llm.client import llm_client
from core.utils import validate_python_code
import logging

logger = logging.getLogger(__name__)

@dataclass
class CodeTask:
    description: str
    context: str = ""

class PythonGenerator:
    def __init__(self, llm: llm_client):
        self.llm = llm

    def generate(self, task: CodeTask) -> Tuple[bool, str]:
        prompt = f"""
        Сгенерируй код на Python по описанию:
        {task.description}
        
        Контекст проекта:
        {task.context}
        
        Требования:
        - Код должен быть полным и готовым к запуску
        - Используй актуальные версии библиотек
        - Добавь комментарии к сложным участкам
        """
        
        try:
            code = self.llm.call(prompt, task.context)
            is_valid, error = validate_python_code(code)
            return (True, code) if is_valid else (False, error)
        except Exception as e:
            logger.error(f"Generation error: {e}")
            return False, f"Generation failed: {str(e)}"