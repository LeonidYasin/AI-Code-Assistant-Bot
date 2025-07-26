import os
import httpx
import asyncio

async def main():
    # 1. Получение токена из переменных окружения
    token = os.getenv("HF_TOKEN")  # Рекомендуемое имя переменной
    if not token:
        print("Ошибка: HF_TOKEN не установлен!")
        print("Получите токен: https://huggingface.co/settings/tokens")
        return

    # 2. Актуальные параметры запроса
    url = "https://api-inference.huggingface.co/models/deepseek-ai/deepseek-coder-6.7b-instruct"  # Используйте конкретную модель
    headers = {"Authorization": f"Bearer {token}"}
    
    payload = {
        "inputs": "Сколько будет 2+2? Ответь по-русски.",  # Формат для text-generation
        "parameters": {
            "max_new_tokens": 64,
            "temperature": 0.3,
            "return_full_text": False  # Не возвращать исходный промпт
        }
    }

    # 3. Увеличенный таймаут для тяжелых моделей
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()  # Проверка HTTP ошибок
            
            # 4. Обработка JSON ответа
            result = response.json()
            print("Статус:", response.status_code)
            
            # 5. Извлечение текста ответа
            if isinstance(result, list) and len(result) > 0:
                generated_text = result[0].get("generated_text", "Ответ не найден")
                print("Ответ:", generated_text)
            else:
                print("Неожиданный формат ответа:", result)
                
        except httpx.HTTPStatusError as e:
            print(f"HTTP ошибка: {e.response.status_code}")
            print("Детали:", e.response.text)
        except Exception as e:
            print(f"Ошибка: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())