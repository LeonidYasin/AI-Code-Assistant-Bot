from typing import Dict, Any, Optional, List, Tuple
import json
import logging
from pathlib import Path

from core.project.manager import ProjectManager

logger = logging.getLogger(__name__)

class ProjectAI:
    def __init__(self, llm_client, project_manager: ProjectManager):
        self.llm = llm_client
        self.pm = project_manager
        
    async def process_request(self, user_request: str) -> Tuple[bool, str]:
        """Process user request and return (success, response)"""
        try:
            # First, analyze the request to determine the action
            action = await self._determine_action(user_request)
            
            if action["action"] == "list_files":
                return await self._handle_list_files()
                
            elif action["action"] == "read_file":
                return await self._handle_read_file(action["file_path"])
                
            elif action["action"] == "write_file":
                return await self._handle_write_file(
                    action["file_path"], 
                    action["content"],
                    action.get("overwrite", False)
                )
                
            elif action["action"] == "execute_script":
                return await self._handle_execute_script(action["file_path"])
                
            elif action["action"] == "analyze_code":
                return await self._handle_analyze_code(
                    action["code"], 
                    action.get("context", "")
                )
                
            else:
                return False, "Неизвестная команда. Пожалуйста, уточните ваш запрос."
                
        except Exception as e:
            logger.error(f"Error processing request: {e}", exc_info=True)
            return False, f"Произошла ошибка: {str(e)}"
    
    async def _determine_action(self, user_request: str) -> Dict[str, Any]:
        """Use LLM to determine the action from user request"""
        prompt = (
            "Ты - AI ассистент для управления локальными проектами через Telegram бота. "
            "Проекты хранятся в локальной директории на сервере. "
            "Анализируй запрос пользователя и возвращай JSON с полями:\n"
            "- 'action': команда для выполнения (create_project, switch_project, list_projects, "
            "list_files, read_file, write_file, execute_script, analyze_code, unknown)\n"
            "- 'project_name': имя проекта (если применимо)\n"
            "- 'file_path': путь к файлу (если применимо)\n"
            "- 'content': содержимое для записи (если применимо)\n"
            "- 'overwrite': перезаписать файл (true/false, по умолчанию false)\n"
            "- 'code': код для анализа (если применимо)\n"
            "- 'needs_confirmation': требуется ли подтверждение (true/false)\n"
            "- 'confirmation_message': сообщение для подтверждения (если needs_confirmation=true)\n"
            "- 'context': дополнительный контекст (если применимо)\n\n"
            "Примеры:\n"
            "1. Запрос: 'Создай проект TestProject'\n"
            "Ответ: {\"action\": \"create_project\", \"project_name\": \"TestProject\", "
            "\"needs_confirmation\": true, \"confirmation_message\": \"Создать проект TestProject?\"}\n\n"
            "2. Запрос: 'Покажи файлы в проекте'\n"
            "Ответ: {\"action\": \"list_files\"}\n\n"
            "3. Запрос: 'Покажи мои проекты'\n"
            "Ответ: {\"action\": \"list_projects\"}\n\n"
            "4. Запрос: 'Проанализируй код: def hello(): return \\\"Hello\\\"'\n"
            "Ответ: {\"action\": \"analyze_code\", \"code\": \"def hello(): return \\\"Hello\\\"\"}\n\n"
            "5. Запрос: 'Переключись на проект MyApp'\n"
            "Ответ: {\"action\": \"switch_project\", \"project_name\": \"MyApp\", "
            "\"needs_confirmation\": true, \"confirmation_message\": \"Переключиться на проект MyApp?\"}\n\n"
            f"Запрос пользователя: {user_request}\n\n"
            "Ответ (только JSON, без дополнительного текста):"
        )
        
        try:
            # Get response from LLM
            response = self.llm.call(prompt, is_json=True)
            
            # Parse the response
            if isinstance(response, str):
                # Extract JSON from response if it's a string
                json_start = response.find('{')
                json_end = response.rfind('}') + 1
                if json_start >= 0 and json_end > 0:
                    response = response[json_start:json_end]
                try:
                    result = json.loads(response)
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse JSON from response: {response}")
                    result = {"action": "unknown"}
            else:
                result = response
                
            # Ensure required fields exist
            if not isinstance(result, dict):
                result = {"action": "unknown"}
                
            # Set default values
            result.setdefault("needs_confirmation", False)
            result.setdefault("confirmation_message", "")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in _determine_action: {e}", exc_info=True)
            return {"action": "unknown"}
    
    async def _handle_list_files(self) -> Tuple[bool, str]:
        files = self.pm.list_files()
        if not files:
            return True, "В проекте пока нет файлов."
            
        file_list = "\n".join([f"- {f['path']} ({f['size']} bytes)" for f in files])
        return True, f"Файлы в проекте:\n{file_list}"
    
    async def _handle_read_file(self, file_path: str) -> Tuple[bool, str]:
        success, content = self.pm.read_file(file_path)
        if not success:
            return False, content
            
        # Truncate large files for display
        max_length = 2000
        if len(content) > max_length:
            content = content[:max_length] + "\n\n... (файл обрезан)"
            
        return True, f"Содержимое файла {file_path}:\n```\n{content}\n```"
    
    async def _handle_write_file(self, file_path: str, content: str, overwrite: bool) -> Tuple[bool, str]:
        success, message = self.pm.write_file(file_path, content, overwrite)
        if not success:
            return False, message
            
        # Verify file was written
        verify_success, verify_content = self.pm.read_file(file_path)
        if not verify_success:
            return False, f"Файл создан, но не удалось его прочитать: {verify_content}"
            
        return True, f"Файл успешно сохранён: {file_path}"
    
    async def _handle_execute_script(self, file_path: str) -> Tuple[bool, str]:
        success, stdout, stderr = self.pm.execute_script(file_path)
        if not success:
            return False, f"Ошибка при выполнении скрипта:\n{stderr}"
            
        output = f"Скрипт выполнен успешно. Вывод:\n{stdout}"
        if stderr:
            output += f"\n\nПредупреждения:\n{stderr}"
            
        return True, output
    
    async def _handle_analyze_code(self, code: str, context: str = "") -> Tuple[bool, str]:
        prompt = (
            "Проанализируй предоставленный код и дай развёрнутый отчёт. "
            f"Контекст: {context}\n\n"
            f"Код для анализа:\n```python\n{code}\n```\n\n"
            "В своём ответе укажи:\n"
            "1. Что делает этот код?\n"
            "2. Есть ли в нём ошибки или потенциальные проблемы?\n"
            "3. Как можно его улучшить?\n"
            "4. Приведи оптимизированную версию, если это уместно."
        )
        
        response = self.llm.call(prompt)
        return True, f"🔍 Анализ кода:\n\n{response}"
