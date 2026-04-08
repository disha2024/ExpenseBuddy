from fastapi_users import schemas as fu_schemas
from pydantic import BaseModel, Field
from datetime import date as date_type, datetime  # We import the 'datetime' class directly
from typing import Optional, Union

# ── USER SCHEMAS (FastAPI Users)
class UserRead(fu_schemas.BaseUser[int]):
    username: str
    joined_at: datetime
    profile_picture: Optional[str] = None
    currency: Optional[str] = "₹"
    
    class Config:
        from_attributes = True

class UserCreate(fu_schemas.BaseUserCreate):
    username: str

class UserUpdate(fu_schemas.BaseUserUpdate):
    username: Optional[str] = None
    profile_picture: Optional[str] = None
    currency: Optional[str] = None


# ── TOKEN SCHEMA
class Token(BaseModel):
    access_token: str
    token_type: str


# ── PROFILE SCHEMAS
class ProfileUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

class CurrencyUpdate(BaseModel):
    currency: str


# ── EXPENSE SCHEMAS
class ExpenseCreate(BaseModel):
    title: str
    amount: float = Field(gt=0)
    category: str
    date: Union[date_type, None] = None

class ExpenseUpdate(BaseModel):
    title: Union[str, None] = None
    amount: Union[float, None] = Field(default=None, gt=0)
    category: Union[str, None] = None
    date: Union[date_type, None] = None

class ExpenseResponse(BaseModel):
    id: int
    title: str
    amount: float
    category: str
    date: Union[date_type, None] = None

    class Config:
        from_attributes = True