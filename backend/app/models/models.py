from sqlmodel import SQLModel, Field
from typing import Optional
import datetime  # Import the whole module instead of 'from datetime import date'
from sqlalchemy import Column, DateTime, func
from decimal import Decimal
#from sqlmodel import SQLModel, Field, Column, Decimal as SQLDecimal


class User(SQLModel, table=True):
    __tablename__: str = "users"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    username: str
    joined_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    created_at: datetime.datetime = Field(
        sa_column=Column(DateTime, server_default=func.now(), nullable=False)
    )
    # --- REQUIRED BY FASTAPI USERS ---
    hashed_password: str = Field(nullable=False)
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    is_verified: bool = Field(default=False)
    # ---------------------------------
    
    profile_picture: Optional[str] = Field(default=None)
    currency: Optional[str] = Field(default="INR")        

class Category(SQLModel, table=True):
    __tablename__: str = "categories"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)  # Unique per user? Wait, for now global, but can add user_id later
    user_id: int = Field(foreign_key="users.id")  # Make it per user

class Expense(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    amount: Decimal = Field(default=0, max_digits=10, decimal_places=10)
    category_id: int = Field(foreign_key="categories.id")
    
    # Use datetime.date to avoid clashing with the field name 'date'
    date: datetime.date = Field(default_factory=datetime.date.today)
    
    user_id: int = Field(foreign_key="users.id")