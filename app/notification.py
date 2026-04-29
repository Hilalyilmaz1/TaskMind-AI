import requests
import os
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv() # 2. Bu fonksiyonu çağır

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

if not TELEGRAM_TOKEN or not CHAT_ID:
    #raise ValueError("Telegram config missing!")
    print("Telegram config missing! Notifications will not work.")

def send_telegram(message:str):
    url=f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    payload={
        "chat_id": CHAT_ID,
        "text": message
    }

    requests.post(url, json=payload)

print("TOKEN:", TELEGRAM_TOKEN)
print("CHAT:", CHAT_ID)