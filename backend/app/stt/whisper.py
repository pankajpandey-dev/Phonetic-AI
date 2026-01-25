import io
import wave
from openai import OpenAI
from app.core.config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

def pcm16_to_wav_bytes(pcm_data: bytes, sample_rate: int = 16000) -> io.BytesIO:
    wav_io = io.BytesIO()
    with wave.open(wav_io, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)  # 16-bit PCM
        wf.setframerate(sample_rate)
        wf.writeframes(pcm_data)

    wav_io.seek(0)
    return wav_io


def transcribe_pcm(pcm_data: bytes) -> str:
    wav_file = pcm16_to_wav_bytes(pcm_data)

    result = client.audio.transcriptions.create(
        file=("audio.wav", wav_file),
        model="whisper-1",
    )

    return result.text.strip()
