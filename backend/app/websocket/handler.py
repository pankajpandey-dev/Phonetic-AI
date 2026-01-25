import asyncio
from app.llm.chat import generate_reply
from app.tts.tts import send_streaming_tts
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.audio.buffer import AudioBuffer
from app.stt.whisper import transcribe_pcm

websocket_router = APIRouter()

@websocket_router.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    print("Client connected")

    audio_buffer = AudioBuffer(silence_seconds=1.0)

    try:
        while True:
            try:
                # IMPORTANT: timeout allows silence detection
                message = await asyncio.wait_for(ws.receive(), timeout=0.2)
            except asyncio.TimeoutError:
                message = None
            except WebSocketDisconnect:
                print("Client disconnected")
                break

            # If we received audio
            if message and "bytes" in message:
                audio_buffer.add_chunk(message["bytes"])

            # Check silence OUTSIDE receive
            if audio_buffer.should_process():
                pcm_audio = audio_buffer.consume()
                print(f"Audio ready: {len(pcm_audio)} bytes")

                try:
                    text = transcribe_pcm(pcm_audio)
                    print("USER SAID:", text)

                except Exception as e:
                    print("STT error:", e)
                    
                try:
                    reply = generate_reply(text)
                    print("ASSISTANT:", reply)
                except Exception as e:
                    print("LLM error:", e)
                    
                await ws.send_text(reply)
                
                await send_streaming_tts(ws, reply)




    finally:
        print("WebSocket cleanup complete")
