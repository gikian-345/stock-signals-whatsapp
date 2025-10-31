import os
from twilio.rest import Client

from messenger_telegram import send_telegram as send_message

def send_whatsapp_message(to_number: str, body: str) -> None:
    sid = os.environ["TWILIO_ACCOUNT_SID"]
    token = os.environ["TWILIO_AUTH_TOKEN"]
    from_number = os.environ.get("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")  # Twilio sandbox
    Client(sid, token).messages.create(from_=from_number, to=to_number, body=body)
