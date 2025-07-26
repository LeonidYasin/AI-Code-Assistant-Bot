import os
import httpx
import asyncio

async def main():
    token = os.getenv("HF_TOKEN")
    if not token:
        print("HF_TOKEN not set!")
        return
    url = "https://router.huggingface.co/v1/models"
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.get(url, headers=headers)
        print(f"Status: {r.status_code}")
        try:
            data = r.json()
            if isinstance(data, dict) and "data" in data:
                models = data["data"]
            else:
                models = data
            for m in models:
                if isinstance(m, dict):
                    print(f"{m.get('id', m)}: {m.get('description', '')}")
                else:
                    print(m)
        except Exception:
            print(r.text)

if __name__ == "__main__":
    asyncio.run(main()) 