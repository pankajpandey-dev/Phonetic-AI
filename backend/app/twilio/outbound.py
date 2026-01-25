from twilio.rest import Client
from app.core.config import settings
import os

client = Client(
    settings.TWILIO_ACCOUNT_SID,
    settings.TWILIO_AUTH_TOKEN
)
print("call details",settings.VOICE_WEBHOOK_URL)
def make_outbound_call(to_phone: str):
    call = client.calls.create(
        to=to_phone,
        from_=settings.TWILIO_PHONE_NUMBER,
        url=settings.VOICE_WEBHOOK_URL  # Twilio hits this
    )
    return call.sid
