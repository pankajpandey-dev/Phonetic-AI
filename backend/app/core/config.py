from pydantic import BaseSettings

class Settings(BaseSettings):
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_PHONE_NUMBER: str

    PUBLIC_BASE_URL: str
    WS_PATH: str = "/ws"
    VOICE_WEBHOOK_PATH: str = "/voice"
    OPENAI_API_KEY: str
    TWILIO_WS_URL: str

    @property
    def WS_URL(self) -> str:
        return f"{self.PUBLIC_BASE_URL}{self.WS_PATH}"

    @property
    def VOICE_WEBHOOK_URL(self) -> str:
        return f"{self.PUBLIC_BASE_URL}{self.VOICE_WEBHOOK_PATH}"

    class Config:
        env_file = ".env"

settings = Settings()
