from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from fastapi_users.db import SQLAlchemyBaseUserTable
from database import Base


# ── USER MODEL (FastAPI Users) ────────────────────────────────
class User(SQLAlchemyBaseUserTable[int], Base):
    __tablename__ = "users"

    id              = Column(Integer, primary_key=True, index=True)
    # FastAPI Users auto-manages: email, hashed_password, is_active, is_superuser, is_verified
    username        = Column(String(50),  unique=True,  nullable=False)
    profile_picture = Column(String(300), nullable=True, default=None)
    currency        = Column(String(10),  nullable=False, default="₹")
    created_at      = Column(DateTime, server_default=func.now())

    expenses = relationship("Expense", back_populates="owner")


# ── EXPENSE MODEL ─────────────────────────────────────────────
class Expense(Base):
    __tablename__ = "expenses"

    id       = Column(Integer, primary_key=True, index=True)
    title    = Column(String(100), nullable=False)
    amount   = Column(Float,       nullable=False)
    category = Column(String(50))
    date     = Column(Date)
    user_id  = Column(Integer, ForeignKey("users.id"), nullable=False)

    owner = relationship("User", back_populates="expenses")