# app/api/dev.py
from fastapi import APIRouter
from app.twilio.outbound import make_outbound_call

router = APIRouter()

@router.post("/call")
def trigger_call(phone: str):
    sid = make_outbound_call(phone)
    return {
        "status": "calling",
        "call_sid": sid
    }
