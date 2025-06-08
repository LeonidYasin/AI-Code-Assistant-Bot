from typing import Tuple  # Добавьте в начало файла
import ast
import subprocess
import os
import logging




logger = logging.getLogger(__name__)

def validate_python_code(code: str) -> Tuple[bool, str]:
    """Проверяет Python-код на синтаксические ошибки"""
    try:
        ast.parse(code)
        return True, ""
    except SyntaxError as e:
        error_msg = f"Syntax error: {e}"
        logger.error(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"Validation error: {e}"
        logger.error(error_msg)
        return False, error_msg

def save_code(code: str, file_path: str) -> Tuple[bool, str]:
    """Сохраняет код в файл с проверкой синтаксиса"""
    is_valid, error = validate_python_code(code)
    if not is_valid:
        return False, error
    
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(code)
        return True, file_path
    except Exception as e:
        error_msg = f"File save error: {e}"
        logger.error(error_msg)
        return False, error_msg

def safe_execute_command(command: str) -> dict:
    """Безопасно выполняет shell-команду"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            text=True,
            capture_output=True,
            timeout=30
        )
        return {
            "success": True,
            "output": result.stdout,
            "error": result.stderr
        }
    except subprocess.CalledProcessError as e:
        return {
            "success": False,
            "output": e.stdout,
            "error": e.stderr
        }
    except Exception as e:
        return {
            "success": False,
            "output": "",
            "error": str(e)
        }