from sqlmodel import SQLModel, Field
from typing import Optional
import datetime  # Import the whole module instead of 'from datetime import date'


class User(SQLModel, table=True):
    __tablename__: str = "users"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    username: str
    joined_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    # --- REQUIRED BY FASTAPI USERS ---
    hashed_password: str = Field(nullable=False)
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    is_verified: bool = Field(default=False)
    # ---------------------------------
    
    profile_picture: Optional[str] = Field(default=None)
    currency: Optional[str] = Field(default=None)

class Expense(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    amount: float
    category: str
    
    # Use datetime.date to avoid clashing with the field name 'date'
    date: datetime.date = Field(default_factory=datetime.date.today)
    
    user_id: int = Field(foreign_key="users.id")