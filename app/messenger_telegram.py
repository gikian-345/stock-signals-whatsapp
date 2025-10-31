import os, requests

def send_telegram(body: str) -> None:
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": body[:3900],   # keep well under Telegram’s 4096 char limit
        "disable_web_page_preview": True,
        "parse_mode": "Markdown"
    }
    r = requests.post(url, json=payload, timeout=30)
    if r.status_code >= 400:
        raise RuntimeError(f"Telegram error {r.status_code}: {r.text}")
