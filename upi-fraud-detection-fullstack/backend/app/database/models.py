from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from .db import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    mobile = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    role = Column(String, default="USER")
    created_at = Column(DateTime, default=datetime.utcnow)
    transactions = relationship("Transaction", back_populates="user")

class Merchant(Base):
    __tablename__ = "merchants"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    upi_id = Column(String, unique=True, index=True)
    category = Column(String, default="GENERAL")
    created_at = Column(DateTime, default=datetime.utcnow)
    transactions = relationship("Transaction", back_populates="merchant")

class Admin(Base):
    __tablename__ = "admin"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True)
    role = Column(String, default="ADMIN")

class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    merchant_id = Column(Integer, ForeignKey("merchants.id"))
    amount = Column(Float, nullable=False)
    ts = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="SUCCESS")
    channel = Column(String, default="UPI")
    risk_score = Column(Float, default=0.0)
    is_fraud = Column(Boolean, default=False)

    user = relationship("User", back_populates="transactions")
    merchant = relationship("Merchant", back_populates="transactions")

class OTPLog(Base):
    __tablename__ = "otp_logs"
    id = Column(Integer, primary_key=True, index=True)
    mobile = Column(String, index=True)
    email = Column(String, index=True)
    otp = Column(String)
    ts = Column(DateTime, default=datetime.utcnow)
    verified = Column(Boolean, default=False)

class FraudLog(Base):
    __tablename__ = "fraud_logs"
    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, index=True)
    risk_score = Column(Float)
    level = Column(String)
    reason = Column(String)
    ts = Column(DateTime, default=datetime.utcnow)
