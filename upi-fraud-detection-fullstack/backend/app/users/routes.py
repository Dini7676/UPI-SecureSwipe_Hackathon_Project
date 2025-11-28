from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from ..database.db import get_db
from ..database.models import User, Transaction

router = APIRouter()

class UserUpdate(BaseModel):
    name: str | None = None
    email: str | None = None

@router.get("/")
def list_users(db: Session = Depends(get_db)):
    return [
        {"id": u.id, "name": u.name, "mobile": u.mobile, "email": u.email, "role": u.role}
        for u in db.query(User).all()
    ]

@router.get("/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    u = db.query(User).get(user_id)
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    return {"id": u.id, "name": u.name, "mobile": u.mobile, "email": u.email, "role": u.role}

@router.put("/{user_id}")
def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db)):
    u = db.query(User).get(user_id)
    if not u:
        raise HTTPException(status_code=404, detail="User not found")
    if payload.name:
        u.name = payload.name
    if payload.email:
        u.email = payload.email
    db.commit()
    return {"message": "updated"}

@router.get("/{user_id}/transactions")
def user_transactions(user_id: int, db: Session = Depends(get_db)):
    txs = db.query(Transaction).filter(Transaction.user_id == user_id).all()
    return [
        {
            "id": t.id,
            "amount": t.amount,
            "ts": t.ts.isoformat(),
            "merchant_id": t.merchant_id,
            "risk_score": t.risk_score,
            "is_fraud": t.is_fraud,
        }
        for t in txs
    ]
