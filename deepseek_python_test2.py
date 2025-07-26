import os
import asyncio
from openai import AsyncOpenAI

async def main():
    client = AsyncOpenAI(
        base_url="https://router.huggingface.co/v1",
        api_key=os.getenv("HF_TOKEN")
    )
    
    try:
        completion = await client.chat.completions.create(
            model="deepseek-ai/deepseek-coder-33b-instruct",
            messages=[{"role": "user", "content": "Привет! Кто ты?"}],
            max_tokens=128,
            temperature=0.7,
            top_p=0.9,
            stream=True  # Для потоковой передачи
        )
        
        async for chunk in completion:
            if chunk.choices[0].delta.content:
                print(chunk.choices[0].delta.content, end="", flush=True)
                
    except Exception as e:
        print(f"\nОшибка: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())