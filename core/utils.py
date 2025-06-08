import ast
import os
import subprocess
import logging
from typing import Tuple

logger = logging.getLogger(__name__)

def is_valid_python(code: str) -> bool:
    """Проверка синтаксиса Python кода"""
    try:
        ast.parse(code)
        return True
    except SyntaxError as e:
        logger.warning(f"Syntax error: {e}")
        return False

def save_code(code: str, file_path: str) -> Tuple[bool, str]:
    """Безопасное сохранение кода"""
    try:
        if not is_valid_python(code):
            return False, "⚠️ Синтаксическая ошибка в коде"
        
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(code)
        return True, file_path
    
    except Exception as e:
        logger.error(f"Save file error: {e}")
        return False, f"❌ Ошибка сохранения: {str(e)}"

def safe_execute_command(command: str) -> str:
    """Безопасное выполнение shell-команд"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            text=True,
            capture_output=True,
            timeout=60
        )
        output = f"STDOUT:\n{result.stdout}"
        if result.stderr:
            output += f"\nSTDERR:\n{result.stderr}"
        return output
    
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {e}")
        return f"⚠️ Ошибка выполнения:\n{e.stderr}"
    except Exception as e:
        logger.error(f"Execution error: {e}")
        return f"⛔ Критическая ошибка: {str(e)}"