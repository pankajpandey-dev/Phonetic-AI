# app/websocket/twilio_handler.py

import json
import base64
import audioop
import asyncio
import time

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.audio.buffer import AudioBuffer
from app.stt.whisper import transcribe_pcm
from app.llm.chat import generate_reply
from app.tts.twilio_streaming import stream_tts_to_twilio
from app.tts.tts import text_to_speech

twilio_ws_router = APIRouter()

@twilio_ws_router.websocket("/twilio/ws")
async def twilio_ws(ws: WebSocket):
    await ws.accept()
    print("Twilio WebSocket connected")

    audio_buffer = AudioBuffer(silence_seconds=1.0)
    stream_sid = None
    listening_start_time = None
    listen_duration = 2.0  # Listen for 2 seconds of silence
    is_listening = False

    try:
        while True:
            try:
                message = await asyncio.wait_for(ws.receive_text(), timeout=0.1)
                data = json.loads(message)
                event = data.get("event")

                if event == "start":
                    start_data = data.get("start", {})
                    stream_sid = start_data.get("streamSid") or data.get("streamSid")
                    print(f"Stream started - SID: {stream_sid}")
                    
                    # Send welcome message
                    try:
                        greeting = "Welcome How can i assist you."
                        pcm_audio = await text_to_speech(greeting)
                        await stream_tts_to_twilio(ws, pcm_audio, stream_sid)
                    except Exception as e:
                        print(f"Error sending greeting: {e}")
                    
                    listening_start_time = time.time()
                    is_listening = True
                    continue

                if event == "media":
                    track = data.get("media", {}).get("track", "inbound")
                    if track != "inbound":
                        continue
                    
                    if "payload" not in data.get("media", {}):
                        continue
                    
                    payload = data["media"]["payload"]
                    mulaw = base64.b64decode(payload)
                    pcm8k = audioop.ulaw2lin(mulaw, 2)
                    pcm16k, _ = audioop.ratecv(pcm8k, 2, 1, 8000, 16000, None)
                    audio_buffer.add_chunk(pcm16k)
                    
                    # Check if we should process (after silence or buffer full)
                    if is_listening and listening_start_time:
                        elapsed = time.time() - listening_start_time
                        if elapsed >= listen_duration or audio_buffer.should_process():
                            is_listening = False
                            
                            if len(audio_buffer.buffer) > 0:
                                pcm_audio = audio_buffer.consume()
                                text = transcribe_pcm(pcm_audio)
                                print(f"USER: {text}")

                                reply = generate_reply(text)
                                print(f"ASSISTANT: {reply}")

                                # Limit response length
                                if len(reply) > 300:
                                    reply = reply[:300] + "..."

                                pcm_audio = await text_to_speech(reply)
                                await stream_tts_to_twilio(ws, pcm_audio, stream_sid)
                                
                                # Reset for next cycle
                                listening_start_time = time.time()
                                is_listening = True
                    continue

                if event == "stop":
                    print("Call ended")
                    break

            except asyncio.TimeoutError:
                # Check if we should process after silence period
                if is_listening and listening_start_time:
                    elapsed = time.time() - listening_start_time
                    if elapsed >= listen_duration and len(audio_buffer.buffer) > 0:
                        is_listening = False
                        pcm_audio = audio_buffer.consume()
                        text = transcribe_pcm(pcm_audio)
                        print(f"USER: {text}")

                        reply = generate_reply(text)
                        print(f"ASSISTANT: {reply}")

                        if len(reply) > 300:
                            reply = reply[:300] + "..."

                        pcm_audio = await text_to_speech(reply)
                        await stream_tts_to_twilio(ws, pcm_audio, stream_sid)
                        
                        listening_start_time = time.time()
                        is_listening = True
                continue

    except WebSocketDisconnect:
        print("Twilio disconnected")
    except Exception as e:
        print(f"Error: {e}")
        raise
