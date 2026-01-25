# app/twilio/voice.py

from fastapi import APIRouter
from fastapi.responses import PlainTextResponse
from twilio.twiml.voice_response import VoiceResponse, Connect, Stream
from app.core.config import settings

twilio_router = APIRouter()

@twilio_router.post("/voice")
async def voice_webhook():
    response = VoiceResponse()

    # CRITICAL: Use Connect with Stream (not Start)
    # This properly establishes Media Stream and triggers the "start" event
    connect = Connect()
    stream = Stream(url=settings.TWILIO_WS_URL)
    # Track parameter is optional - defaults to both_tracks
    stream.parameter(name="track", value="both_tracks")
    connect.append(stream)
    response.append(connect)

    # Keep call open - WebSocket handles all audio
    response.pause(length=3600)

    return PlainTextResponse(
        str(response),
        media_type="application/xml"
    )
