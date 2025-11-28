from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from datetime import timedelta
from ..database.redis_client import get_redis
from ..database.db import get_db
from ..database.models import User, OTPLog
from sqlalchemy.orm import Session
from .utils import create_access_token
import random

router = APIRouter()

class SendOTPRequest(BaseModel):
    mobile: str
    email: str | None = None

class VerifyOTPRequest(BaseModel):
    mobile: str
    email: str | None = None
    otp: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str

@router.post("/send-otp")
def send_otp(payload: SendOTPRequest, db: Session = Depends(get_db)):
    r = get_redis()
    otp = f"{random.randint(100000, 999999)}"
    key = f"otp:{payload.mobile}:{payload.email or ''}"
    r.setex(key, 300, otp)
    log = OTPLog(mobile=payload.mobile, email=payload.email, otp=otp)
    db.add(log)
    db.commit()
    # In production, send via SMS/Email provider
    return {"message": "OTP sent", "otp_debug": otp}

@router.post("/verify-otp", response_model=TokenResponse)
def verify_otp(payload: VerifyOTPRequest, db: Session = Depends(get_db)):
    r = get_redis()
    key = f"otp:{payload.mobile}:{payload.email or ''}"
    otp_val = r.get(key)
    if not otp_val or otp_val.decode() != payload.otp:
        raise HTTPException(status_code=400, detail="Invalid or expired OTP")
    r.delete(key)

    user = db.query(User).filter(User.mobile == payload.mobile).first()
    if not user:
        user = User(name=f"User-{payload.mobile}", mobile=payload.mobile, email=payload.email, role="USER")
        db.add(user)
        db.commit()
        db.refresh(user)

    token = create_access_token({"sub": str(user.id), "role": user.role}, expires_delta=timedelta(hours=2))

    log = db.query(OTPLog).filter(OTPLog.mobile == payload.mobile, OTPLog.otp == payload.otp).first()
    if log:
        log.verified = True
        db.commit()

    return TokenResponse(access_token=token, role=user.role)
