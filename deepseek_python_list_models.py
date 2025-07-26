import os
import httpx
import asyncio
from pprint import pprint

async def get_programming_chat_models():
    """Получает список чат-моделей, пригодных для программирования"""
    token = os.getenv("HF_TOKEN")
    if not token:
        raise ValueError("HF_TOKEN environment variable not set!")
    
    url = "https://router.huggingface.co/models"
    headers = {"Authorization": f"Bearer {token}"}
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            models_data = response.json()
            
            # Фильтруем модели для программирования
            programming_models = []
            programming_keywords = [
                "code", "coder", "program", "python", "java", "javascript",
                "instruct", "coding", "dev", "develop", "sql", "html"
            ]
            
            for model in models_data:
                # Проверяем, что это текстовая модель и поддерживает чат
                if model.get("task") != "text-generation":
                    continue
                
                model_id = model.get("id", "").lower()
                
                # Проверяем ключевые слова в названии модели
                is_programming_model = any(
                    keyword in model_id for keyword in programming_keywords
                )
                
                # Дополнительные проверки для популярных моделей
                is_known_programming_model = any(
                    model_id.startswith(prefix) for prefix in [
                        "deepseek-ai/deepseek-coder",
                        "bigcode/starcoder",
                        "codellama/codellama",
                        "microsoft/phi",
                        "google/codegemma",
                        "mistralai/codestral"
                    ]
                )
                
                if is_programming_model or is_known_programming_model:
                    programming_models.append({
                        "id": model["id"],
                        "task": model["task"],
                        "framework": model.get("framework", "unknown"),
                        "provider": model.get("provider", "unknown")
                    })
            
            return programming_models
            
        except httpx.HTTPStatusError as e:
            print(f"HTTP error {e.response.status_code}: {e.response.text}")
            return []
        except Exception as e:
            print(f"Error: {str(e)}")
            return []

async def main():
    print("Получаю список моделей для программирования...")
    models = await get_programming_chat_models()
    
    if not models:
        print("Не найдено подходящих моделей для программирования")
        return
    
    print("\nДоступные модели для программирования:")
    for i, model in enumerate(models, 1):
        print(f"{i}. {model['id']}")
        print(f"   Framework: {model['framework']}")
        print(f"   Provider: {model['provider']}")
        print(f"   Task: {model['task']}\n")
    
    print(f"Всего найдено моделей: {len(models)}")

if __name__ == "__main__":
    asyncio.run(main())