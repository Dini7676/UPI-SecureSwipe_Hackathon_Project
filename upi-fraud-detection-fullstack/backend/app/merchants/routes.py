from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..database.db import get_db
from ..database.models import Merchant, Transaction

router = APIRouter()

class MerchantCreate(BaseModel):
    name: str
    upi_id: str
    category: str | None = "GENERAL"

@router.get("/")
def list_merchants(db: Session = Depends(get_db)):
    return [
        {"id": m.id, "name": m.name, "upi_id": m.upi_id, "category": m.category}
        for m in db.query(Merchant).all()
    ]

@router.post("/")
def create_merchant(payload: MerchantCreate, db: Session = Depends(get_db)):
    m = Merchant(name=payload.name, upi_id=payload.upi_id, category=payload.category)
    db.add(m)
    db.commit()
    db.refresh(m)
    return {"id": m.id}

@router.get("/{merchant_id}/transactions")
def merchant_transactions(merchant_id: int, db: Session = Depends(get_db)):
    txs = db.query(Transaction).filter(Transaction.merchant_id == merchant_id).all()
    return [
        {
            "id": t.id,
            "amount": t.amount,
            "ts": t.ts.isoformat(),
            "user_id": t.user_id,
            "risk_score": t.risk_score,
            "is_fraud": t.is_fraud,
        }
        for t in txs
    ]
