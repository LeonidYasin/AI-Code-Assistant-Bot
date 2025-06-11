import requests
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
url = f"https://api.telegram.org/bot{TOKEN}/getWebhookInfo"

response = requests.get(url).json()
print("Webhook info:")
print(response)
