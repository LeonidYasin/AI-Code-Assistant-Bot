#!/usr/bin/env python3
"""
Простая загрузка переменных окружения из .env файла
"""
import os

def load_env_file(filename=".env"):
    """Загружает переменные окружения из файла"""
    if not os.path.exists(filename):
        print(f"Warning: {filename} file not found")
        return
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    os.environ[key] = value
                    print(f"Loaded: {key}={'*' * len(value)}")
    except Exception as e:
        print(f"Error loading {filename}: {e}")

if __name__ == "__main__":
    load_env_file()
    print(f"PROVIDER: {os.getenv('PROVIDER', 'not set')}")
    print(f"HF_TOKEN: {'set' if os.getenv('HF_TOKEN') else 'not set'}")