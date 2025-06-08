from dataclasses import dataclass
from core.llm.client import LLMClient
from core.utils import validate_python_code
import logging

logger = logging.getLogger(__name__)

@dataclass
class CodeTask:
    description: str  # "напиши парсер CSV"
    context: str = "" # Контекст проекта

class PythonGenerator:
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def generate(self, task: CodeTask) -> tuple[str, str]:
        """Генерирует код и возвращает (статус, результат)"""
        prompt = f"""
        Сгенерируй код на Python. Требования:
        {task.description}
        Контекст проекта:
        {task.context}
        Код должен быть готов к запуску без доработок.
        """
        
        try:
            code = self.llm.call(prompt, task.context)
            is_valid, error = validate_python_code(code)
            return ("success", code) if is_valid else ("error", error)
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            return ("error", f"Ошибка генерации: {str(e)}")