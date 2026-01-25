import time

class AudioBuffer:
    def __init__(self, silence_seconds: float = 1.0, max_buffer_size: int = 160000):
        """
        Args:
            silence_seconds: Process audio after this many seconds of silence
            max_buffer_size: Process audio if buffer exceeds this size (bytes)
                            Default ~5 seconds at 16kHz PCM16
        """
        self.buffer = bytearray()
        self.last_audio_time = time.time()
        self.silence_seconds = silence_seconds
        self.max_buffer_size = max_buffer_size

    def add_chunk(self, data: bytes):
        self.buffer.extend(data)
        self.last_audio_time = time.time()

    def should_process(self) -> bool:
        if not self.buffer:
            return False
        # Process if silence detected OR buffer is too large
        silence_detected = (time.time() - self.last_audio_time) > self.silence_seconds
        buffer_full = len(self.buffer) > self.max_buffer_size
        return silence_detected or buffer_full

    def consume(self) -> bytes:
        data = bytes(self.buffer)
        self.buffer.clear()
        return data
