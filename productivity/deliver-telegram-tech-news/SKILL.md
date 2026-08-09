---
name: deliver-telegram-tech-news
description: "Sends tech news to Telegram, splits messages, cleans cache."
---

# Deliver Telegram Tech News

This skill delivers a formatted tech news digest to a Telegram chat, handling message splitting and post-delivery state management.

### Setup

1. Ensure environment variables are set:
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`

2. Place the following script at `/opt/tech-news-bot/deliver.py`:

```python
import os
import requests
import json
import logging

# Configuration
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
BRIEFING_FILE = "/cache/formatted_briefing.txt"
SENT_URLS_FILE = "/history/sent_urls.json"
TOP_NEWS_FILE = "/cache/top_5_news.json"
LOG_FILE = "/logs/delivery.log"

logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format='%(asctime)s - %(message)s')

def split_message(text, limit=4096):
    messages = []
    while len(text) > limit:
        split_idx = text.rfind('\n\n', 0, limit)
        if split_idx == -1: split_idx = limit
        messages.append(text[:split_idx])
        text = text[split_idx:].lstrip()
    messages.append(text)
    return messages

def send_telegram():
    try:
        with open(BRIEFING_FILE, 'r', encoding='utf-8') as f:
            content = f.read()
        
        with open(TOP_NEWS_FILE, 'r') as f:
            news_items = json.load(f)
            
        messages = split_message(content)
        
        for msg in messages:
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            # Updated to include labels in the message content
            payload = {"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"}
            response = requests.post(url, json=payload)
            response.raise_for_status()

        # Cleanup & History
        urls = [item['url'] for item in news_items]
        if os.path.exists(SENT_URLS_FILE):
            with open(SENT_URLS_FILE, 'r+') as f:
                history = json.load(f)
                history.extend(urls)
                f.seek(0)
                json.dump(history, f)
        else:
            with open(SENT_URLS_FILE, 'w') as f:
                json.dump(urls, f)

        open(TOP_NEWS_FILE, 'w').close()
        open(BRIEFING_FILE, 'w').close()
        
        logging.info("Delivery successful.")
        print("Delivery successful.")
        
    except Exception as e:
        logging.error(f"Delivery failed: {str(e)}")
        print(f"Error: {e}")

if __name__ == "__main__":
    send_telegram()
```
