import audioop
import base64

def pcm16_to_twilio_payload(pcm16_8khz: bytes) -> str:
    """
    Convert PCM16 @8kHz → μ-law @8kHz → base64
    
    Args:
        pcm16_8khz: PCM16 audio at 8kHz (must be exactly 160 samples = 320 bytes for 20ms)
    
    Returns:
        Base64 encoded μ-law string (~216 chars for 160 bytes)
    """
    # PCM16 @8kHz → μ-law @8kHz
    # Input must be 160 samples (320 bytes) for 20ms frame
    mulaw = audioop.lin2ulaw(pcm16_8khz, 2)  # 2 = 16-bit sample width
    
    # Base64 encode (160 bytes → ~216 chars)
    return base64.b64encode(mulaw).decode("ascii")

def resample_16k_to_8k(pcm16_16khz: bytes) -> bytes:
    """
    Resample PCM16 @16kHz → PCM16 @8kHz
    
    Args:
        pcm16_16khz: PCM16 audio at 16kHz
    
    Returns:
        PCM16 audio at 8kHz (half the size)
    """
    pcm8k, _ = audioop.ratecv(
        pcm16_16khz,
        2,      # sample width (16-bit)
        1,      # mono
        16000,  # input rate
        8000,   # output rate
        None
    )
    return pcm8k
