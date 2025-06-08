import ast
import subprocess
from pathlib import Path

def validate_python_code(code: str) -> tuple[bool, str]:
    """Проверяет код на синтаксис и исполняемость"""
    try:
        ast.parse(code)  # Синтаксис
        test_script = f"from tempfile import TemporaryFile\nwith TemporaryFile('w+') as f:\n    f.write({repr(code)})\n    f.seek(0)\n    exec(f.read())"
        subprocess.run(["python", "-c", test_script], check=True, timeout=5)  # Запуск
        return True, ""
    except SyntaxError as e:
        return False, f"Синтаксическая ошибка: {e}"
    except subprocess.TimeoutExpired:
        return False, "Код выполняется слишком долго (возможна бесконечная петля)"
    except Exception as e:
        return False, f"Ошибка выполнения: {str(e)}"