# Voice Assistant Application

A real-time voice assistant application that supports both web-based microphone input and Twilio phone call integration. The system uses OpenAI's Whisper for speech-to-text, GPT-4 for conversational AI, and OpenAI TTS for text-to-speech synthesis.

## Architecture Overview

The application consists of two main components:

1. **Frontend**: A web-based interface for microphone recording and outbound call initiation
2. **Backend**: FastAPI server handling WebSocket connections, audio processing, and Twilio integration

## System Flow

### Web-Based Voice Interaction Flow

```
User Microphone → WebSocket → Audio Buffer → Whisper STT → GPT-4 LLM → OpenAI TTS → WebSocket → Browser Audio
```

1. **Audio Capture**: Browser captures microphone audio at 16kHz, converts to PCM16 format
2. **WebSocket Streaming**: Audio chunks sent via WebSocket (`/ws` endpoint)
3. **Audio Buffering**: `AudioBuffer` accumulates audio chunks and detects silence
4. **Speech Recognition**: When silence detected, audio is transcribed using OpenAI Whisper
5. **LLM Processing**: Transcribed text is sent to GPT-4 for response generation
6. **Text-to-Speech**: Response text is converted to audio using OpenAI TTS
7. **Audio Playback**: TTS audio streamed back to browser for playback

### Twilio Phone Call Flow

```
Phone Call → Twilio → Voice Webhook → Twilio WebSocket → Audio Buffer → STT → LLM → TTS → Twilio → Phone
```

1. **Call Initiation**: Outbound call triggered via `/api/call` endpoint
2. **Twilio Webhook**: Twilio calls `/voice` endpoint, receives TwiML with WebSocket connection
3. **Media Stream**: Twilio establishes WebSocket connection at `/twilio/ws`
4. **Audio Processing**: Inbound audio (μ-law @ 8kHz) converted to PCM16 @ 16kHz
5. **Silence Detection**: System listens for 2 seconds, then processes accumulated audio
6. **STT/LLM/TTS**: Same pipeline as web-based flow
7. **Audio Streaming**: TTS audio converted to μ-law @ 8kHz and streamed back to Twilio

## Implementation Details

### Backend Structure

#### Core Configuration (`app/core/config.py`)
- Manages environment variables via Pydantic Settings
- Configures Twilio credentials, OpenAI API key, and webhook URLs
- Provides computed properties for WebSocket and webhook URLs

#### Audio Processing (`app/audio/`)

**AudioBuffer (`buffer.py`)**
- Accumulates audio chunks in a byte buffer
- Implements silence detection based on time since last audio chunk
- Processes audio when:
  - Silence detected (configurable duration, default 1 second)
  - Buffer exceeds maximum size (default ~5 seconds at 16kHz)
- Thread-safe buffer management with `consume()` method

**Twilio Audio Conversion (`twilio_audio.py`)**
- `pcm16_to_twilio_payload()`: Converts PCM16 @ 8kHz → μ-law → base64
- `resample_16k_to_8k()`: Resamples PCM16 from 16kHz to 8kHz
- Handles format conversion required by Twilio Media Streams

#### Speech-to-Text (`app/stt/whisper.py`)
- Converts PCM16 audio bytes to WAV format
- Sends to OpenAI Whisper API for transcription
- Returns cleaned text output
- Handles audio format conversion (PCM16 → WAV)

#### Text-to-Speech (`app/tts/`)

**Standard TTS (`tts.py`)**
- `text_to_speech()`: Generates PCM16 @ 16kHz audio from text
  - Attempts direct PCM format from OpenAI API
  - Falls back to MP3 → PCM conversion using pydub if needed
- `send_streaming_tts()`: Streams TTS audio to WebSocket in chunks
  - Splits audio into ~1 second chunks
  - Sends with small delays to simulate real-time streaming

**Twilio Streaming TTS (`twilio_streaming.py`)**
- `stream_tts_to_twilio()`: Sends TTS audio to Twilio in required format
- Converts PCM16 @ 16kHz → PCM16 @ 8kHz → μ-law → base64
- Sends frames of exactly 160 samples (20ms) at 20ms intervals
- Includes mark events to signal end of speech

#### LLM Integration (`app/llm/chat.py`)
- Uses OpenAI GPT-4-mini for conversational responses
- System prompt: "You are a helpful voice assistant"
- Returns assistant's text response

#### WebSocket Handlers (`app/websocket/`)

**Standard WebSocket (`handler.py`)**
- Endpoint: `/ws`
- Accepts binary PCM16 audio chunks from browser
- Uses `AudioBuffer` for silence detection
- Processing pipeline:
  1. Accumulate audio until silence detected
  2. Transcribe with Whisper
  3. Generate reply with GPT-4
  4. Send text response
  5. Stream TTS audio back
- Handles WebSocket disconnections gracefully

**Twilio WebSocket (`twilio_handler.py`)**
- Endpoint: `/twilio/ws`
- Handles Twilio Media Stream WebSocket protocol
- Event types:
  - `start`: Initializes stream, sends welcome message
  - `media`: Processes inbound audio (μ-law → PCM16)
  - `stop`: Handles call termination
- Listens for 2 seconds before processing (configurable)
- Converts Twilio μ-law @ 8kHz to PCM16 @ 16kHz for processing
- Limits responses to 300 characters for phone calls

#### Twilio Integration (`app/twilio/`)

**Voice Webhook (`voice.py`)**
- Endpoint: `/voice` (POST)
- Returns TwiML with `<Connect><Stream>` directive
- Establishes WebSocket connection for media streaming
- Keeps call open with long pause (3600 seconds)

**Outbound Calls (`outbound.py`)**
- `make_outbound_call()`: Initiates Twilio outbound call
- Uses Twilio REST API to create call
- Points to voice webhook URL for call handling

#### API Endpoints (`app/api/call.py`)
- Endpoint: `/api/call` (POST)
- Accepts phone number as query parameter
- Triggers outbound call via Twilio
- Returns call SID and status

#### Main Application (`app/main.py`)
- FastAPI application entry point
- Registers all routers:
  - `/ws` - Standard WebSocket
  - `/twilio/ws` - Twilio WebSocket
  - `/voice` - Twilio voice webhook
  - `/api/call` - Outbound call API
- Health check endpoint at `/`

### Frontend Implementation (`frontend/index.html`)

**Features:**
- Modern, responsive UI with gradient styling
- Real-time status indicators
- Microphone recording controls
- Outbound call interface

**WebSocket Connection:**
- Connects to `ws://localhost:8000/ws`
- Binary mode for audio streaming
- Handles connection errors and disconnections

**Audio Capture:**
- Uses Web Audio API (`AudioContext`)
- Captures at 16kHz sample rate
- Converts Float32 → Int16 PCM
- Sends audio chunks via WebSocket

**Audio Playback:**
- Receives TTS audio chunks from server
- Queues audio chunks for sequential playback
- Automatically pauses microphone during playback
- Resumes recording after playback completes

**Outbound Call:**
- Phone number input with validation
- Calls `/api/call` endpoint with phone number
- Displays call status (success/error)
- Handles CORS and network errors

## Configuration

### Environment Variables

Create a `.env` file in the backend directory:

```env
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_PHONE_NUMBER=your_twilio_phone_number
PUBLIC_BASE_URL=https://your-domain.com
WS_PATH=/ws
VOICE_WEBHOOK_PATH=/voice
OPENAI_API_KEY=your_openai_api_key
TWILIO_WS_URL=wss://your-domain.com/twilio/ws
```

### Dependencies

Key dependencies (see `requirements.txt` for full list):
- `fastapi`: Web framework
- `uvicorn`: ASGI server
- `websockets`: WebSocket support
- `twilio`: Twilio SDK
- `openai`: OpenAI API client
- `pydub`: Audio processing
- `audioop`: Audio format conversion

## Running the Application

1. **Install Dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Configure Environment:**
   - Create `.env` file with required variables
   - Ensure `PUBLIC_BASE_URL` is publicly accessible (for Twilio webhooks)

3. **Start Backend Server:**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

4. **Open Frontend:**
   - Open `frontend/index.html` in a web browser
   - Or serve via a web server

## Audio Format Specifications

### Web-Based Flow
- **Input**: PCM16 @ 16kHz, mono
- **STT Input**: WAV format (converted from PCM16)
- **TTS Output**: PCM16 @ 16kHz (or MP3 converted to PCM16)
- **Playback**: Browser handles PCM16 chunks

### Twilio Flow
- **Input**: μ-law @ 8kHz (from Twilio)
- **Processing**: Converted to PCM16 @ 16kHz for STT
- **TTS Output**: PCM16 @ 16kHz
- **Output**: Converted to μ-law @ 8kHz, base64 encoded
- **Frame Size**: 160 samples (20ms) per frame
- **Frame Rate**: 50 frames/second (20ms intervals)

## Key Design Decisions

1. **Silence Detection**: Uses time-based silence detection rather than energy-based VAD for simplicity
2. **Audio Buffering**: Accumulates audio until silence or buffer limit to improve transcription accuracy
3. **Format Conversion**: Handles multiple audio formats (PCM16, μ-law, WAV, MP3) with appropriate conversions
4. **Streaming TTS**: Chunks TTS audio for real-time playback experience
5. **Error Handling**: Graceful degradation with fallback mechanisms (e.g., MP3 fallback for TTS)
6. **Response Limiting**: Limits phone call responses to 300 characters to prevent long monologues

## Limitations and Considerations

1. **Silence Detection**: Time-based silence detection may not work well in noisy environments
2. **Latency**: Processing pipeline introduces latency (STT + LLM + TTS)
3. **Cost**: Uses OpenAI API for all processing (Whisper, GPT-4, TTS)
4. **Twilio Requirements**: Requires publicly accessible URL for webhooks
5. **Audio Quality**: Phone calls limited to 8kHz sample rate (Twilio constraint)
6. **Concurrent Calls**: Single server instance may struggle with multiple simultaneous calls

## Future Enhancements

- Implement Voice Activity Detection (VAD) for better silence detection
- Add support for multiple concurrent calls
- Implement audio quality improvements
- Add conversation history and context management
- Implement streaming STT for lower latency
- Add support for different TTS voices and languages
- Implement call recording and logging
- Add authentication and rate limiting

