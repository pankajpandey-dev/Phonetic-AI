from fastapi import FastAPI
from app.twilio.voice import twilio_router
from app.websocket.twilio_handler import twilio_ws_router
from app.api.call import router as call_router
from app.websocket.handler import websocket_router
app = FastAPI()
app.include_router(websocket_router)
app.include_router(twilio_ws_router)
app.include_router(twilio_router)
app.include_router(call_router, prefix="/api")

@app.get("/")
def health():
    return {"status": "ok"}
