import asyncio
import io
from openai import OpenAI
from pydub import AudioSegment
from app.core.config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

async def send_streaming_tts(ws, text: str):
    # Generate full audio (or stream if SDK supports)
    response = client.audio.speech.create(
        model="tts-1",
        voice="alloy",
        input=text
    )
    audio_bytes = response.read()  # full audio bytes

    # Split into chunks for streaming
    chunk_size = 16000  # adjust ~1 sec per chunk
    for i in range(0, len(audio_bytes), chunk_size):
        chunk = audio_bytes[i:i+chunk_size]
        await ws.send_bytes(chunk)
        await asyncio.sleep(0.01)  # tiny delay to simulate streaming


async def text_to_speech(text: str) -> bytes:
    """
    Generate TTS audio and return PCM16 bytes @ 16kHz
    """
    try:
        # Try PCM format directly (if supported by your OpenAI API version)
        response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text,
            response_format="pcm"  # Raw PCM format
        )
        pcm_bytes = response.read()
        return pcm_bytes
    except Exception:
        # Fallback: Get MP3 and convert to PCM16
        response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text,
            response_format="mp3"
    )

        # Read MP3 audio
        mp3_audio = response.read()
        
        # Convert MP3 to PCM16 @ 16kHz using pydub
        audio_segment = AudioSegment.from_mp3(io.BytesIO(mp3_audio))
        # Resample to 16kHz, mono, 16-bit
        audio_segment = audio_segment.set_frame_rate(16000).set_channels(1).set_sample_width(2)
        
        # Export as raw PCM16
        pcm_bytes = audio_segment.raw_data
        
        return pcm_bytes
