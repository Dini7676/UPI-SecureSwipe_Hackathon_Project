from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..database.db import get_db
from ..database.models import Transaction, FraudLog
from .engine import rule_score, level_from_score

router = APIRouter()

class FraudRequest(BaseModel):
    user_id: int
    merchant_id: int
    amount: float
    channel: str = "UPI"
    merchant_category: str = "GENERAL"
    user_tx_last_hour: int = 0
    merchant_tx_last_hour: int = 0

@router.post("/score")
def score(payload: FraudRequest, db: Session = Depends(get_db)):
    tx = payload.model_dump()
    s = rule_score(tx)
    level = level_from_score(s)

    t = Transaction(user_id=payload.user_id, merchant_id=payload.merchant_id, amount=payload.amount, channel=payload.channel, risk_score=s, is_fraud=(level == "HIGH"))
    db.add(t)
    db.commit()
    db.refresh(t)

    log = FraudLog(transaction_id=t.id, risk_score=s, level=level, reason="Rule-based")
    db.add(log)
    db.commit()

    return {"transaction_id": t.id, "risk_score": s, "level": level}
