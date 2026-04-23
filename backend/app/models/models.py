from sqlmodel import SQLModel, Field, Relationship, UniqueConstraint 
from typing import Optional,List
import datetime
from sqlalchemy import Column, String, DateTime, func
from decimal import Decimal
from sqlalchemy import Column, String, DateTime, func, Integer, ForeignKey

class User(SQLModel, table=True):
    __tablename__: str = "users"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    username: str
    joined_at: datetime.datetime = Field(default_factory=datetime.datetime.utcnow)
    created_at: datetime.datetime = Field(
        sa_column=Column(DateTime, server_default=func.now(), nullable=False)
    )
    expenses: List["Expense"] = Relationship(
        back_populates="user", 
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    categories: List["Category"] = Relationship(
        back_populates="user", 
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

    # REQUIRED BY FASTAPI USERS
    hashed_password: str = Field(nullable=False)
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    is_verified: bool = Field(default=False)
    
    profile_picture: Optional[str] = Field(default=None)
    
    # Kept the version with explicit Column for DB safety
    currency: str = Field(sa_column=Column(String(10), nullable=False, default="INR"))

class Category(SQLModel, table=True):
    __tablename__: str = "categories"
    __table_args__ = (UniqueConstraint("name", "user_id", name="unique_category_per_user"),)
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True) # Removed unique=True globally since you have user_id
    user_id: int = Field(foreign_key="users.id")
    user: User = Relationship(back_populates="categories")
    expenses: List["Expense"] = Relationship(back_populates="category")


class Expense(SQLModel, table=True):
    __tablename__: str = "expenses"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    amount: int = Field(sa_column=Column("amount", Integer, nullable=False))
    # SQLModel native way (Much safer!)
    category_id: Optional[int] = Field(
        default=None, 
        foreign_key="categories.id", # Points to table_name.column_name
        ondelete="SET NULL"
    )
    
    date: datetime.date = Field(default_factory=datetime.date.today)
    user_id: int = Field(foreign_key="users.id")
    
    # Relationships
    user: "User" = Relationship(back_populates="expenses")
    category: Optional["Category"] = Relationship(back_populates="expenses")
