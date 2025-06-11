"""Test script to check GigaChat model configuration"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import after loading env vars
from config.settings import GIGACHAT_CREDS
from config.models import GIGACHAT_MODELS, DEFAULT_MODEL

print("\n=== GigaChat Configuration Test ===\n")

# Print model info
print(f"[CONFIG] Default model key: {DEFAULT_MODEL}")
print(f"[CONFIG] Model mapping: {GIGACHAT_MODELS}")
print(f"[CONFIG] Selected model: {GIGACHAT_MODELS[DEFAULT_MODEL]}")

# Print credentials info (masked)
print("\n[CREDENTIALS]")
print(f"Credentials provided: {'Yes' if GIGACHAT_CREDS.get('credentials') else 'No'}")
print(f"Model in settings: {GIGACHAT_CREDS.get('model')}")
print("\n=== Test Complete ===\n")
