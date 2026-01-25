import json
import asyncio
from fastapi import WebSocketDisconnect
from app.audio.twilio_audio import pcm16_to_twilio_payload, resample_16k_to_8k

async def stream_tts_to_twilio(ws, pcm_audio_16khz: bytes, stream_sid: str = None):
    """
    Send TTS audio to Twilio in EXACTLY the format Twilio requires.
    
    Requirements:
    - μ-law encoding
    - 8000 Hz sample rate
    - Mono channel
    - 160 samples per frame (20ms)
    - 160 bytes μ-law per frame
    - Base64 payload ~216 chars per frame
    - One frame every 20ms (real-time pacing)
    """
    if not pcm_audio_16khz or len(pcm_audio_16khz) == 0:
        print("Warning: Empty audio, skipping TTS")
        return

    if not stream_sid:
        raise ValueError("streamSid is required to send media")
    
    # Resample entire audio from 16kHz → 8kHz
    pcm_audio_8khz = resample_16k_to_8k(pcm_audio_16khz)
    
    # Limit total audio size (max ~30 seconds)
    MAX_AUDIO_SIZE = 480000  # ~30 seconds @ 8kHz PCM16
    if len(pcm_audio_8khz) > MAX_AUDIO_SIZE:
        pcm_audio_8khz = pcm_audio_8khz[:MAX_AUDIO_SIZE]
    
    # Chunk at 8kHz - EXACTLY 160 samples per frame (20ms)
    FRAME_SIZE = 320  # 160 samples * 2 bytes = 320 bytes PCM16 @ 8kHz = 20ms
    
    for i in range(0, len(pcm_audio_8khz), FRAME_SIZE):
        frame = pcm_audio_8khz[i:i + FRAME_SIZE]
        
        if len(frame) < FRAME_SIZE:
            break
        
        payload = pcm16_to_twilio_payload(frame)
        
        message = {
            "event": "media",
            "streamSid": stream_sid,
            "media": {
                "track": "outbound",
                "payload": payload
            }
        }

        try:
            await ws.send_text(json.dumps(message))
        except (WebSocketDisconnect, RuntimeError, ConnectionError):
            break
        except Exception:
            break

        await asyncio.sleep(0.02)  # 20ms per frame

    # Mark end of speech
    try:
        mark_message = {
            "event": "mark",
            "streamSid": stream_sid,
            "mark": {"name": "assistant_done"}
        }
        await ws.send_text(json.dumps(mark_message))
    except (WebSocketDisconnect, RuntimeError, ConnectionError):
        pass
