from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database.db import get_db
from ..database.models import FraudLog, OTPLog, Transaction

router = APIRouter()

@router.get("/stats")
def stats(db: Session = Depends(get_db)):
    fraud_count = db.query(FraudLog).count()
    otp_sent = db.query(OTPLog).count()
    tx_count = db.query(Transaction).count()
    return {"transactions": tx_count, "frauds": fraud_count, "otp_logs": otp_sent}

@router.get("/fraud-logs")
def get_fraud_logs(db: Session = Depends(get_db)):
    logs = db.query(FraudLog).order_by(FraudLog.ts.desc()).limit(100).all()
    return [
        {
            "id": l.id,
            "transaction_id": l.transaction_id,
            "risk_score": l.risk_score,
            "level": l.level,
            "reason": l.reason,
            "ts": l.ts.isoformat(),
        }
        for l in logs
    ]
