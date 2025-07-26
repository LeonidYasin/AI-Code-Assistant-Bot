import os
import httpx
import asyncio

async def main():
    token = os.getenv("HF_TOKEN")
    if not token:
        print("HF_TOKEN not set!")
        return
    url = "https://router.huggingface.co/v1/chat/completions"
    headers = {"Authorization": f"Bearer {token}"}
    payload = {
        "model": "deepseek-ai/DeepSeek-V3",
        "messages": [
            {"role": "user", "content": "Сколько будет 2+2? Ответь по-русски."}
        ],
        "max_tokens": 64,
        "temperature": 0.3
    }
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(url, headers=headers, json=payload)
        print(f"Status: {r.status_code}")
        try:
            print(r.json())
        except Exception:
            print(r.text)

if __name__ == "__main__":
    asyncio.run(main()) 