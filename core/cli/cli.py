import argparse
import asyncio
import os
import sys
from core.ai import ask

async def analyze(path: str):
    with open(path, encoding="utf-8") as f:
        code = f.read()
    messages = [{"role": "user", "content": f"Проанализируй код:\n{code}"}]
    answer = await ask(messages)
    print(answer)

def main():
    parser = argparse.ArgumentParser(description="AI Code Assistant CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p1 = sub.add_parser("analyze")
    p1.add_argument("path", help="файл или директория")

    p2 = sub.add_parser("switch-model")
    p2.add_argument("provider", choices=["hf_deepseek", "kimi", "gigachat"])

    args = parser.parse_args()
    if args.cmd == "analyze":
        asyncio.run(analyze(args.path))
    elif args.cmd == "switch-model":
        print(f"Переключись вручную в .env: PROVIDER={args.provider}")

if __name__ == "__main__":
    main()