from fastapi_users import schemas as fu_schemas
from pydantic import BaseModel, Field
from datetime import date as date_type, datetime  # We import the 'datetime' class directly
from typing import Optional, Union

# ── USER SCHEMAS (FastAPI Users)
class UserRead(fu_schemas.BaseUser[int]):
    username: str
    joined_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    profile_picture: Optional[str] = None
    currency: Optional[str] = "INR"
    
    class Config:
        from_attributes = True

class UserCreate(fu_schemas.BaseUserCreate):
    username: str
    currency: Optional[str] = "INR"

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


# ── CATEGORY SCHEMAS
class CategoryCreate(BaseModel):
    name: str

class CategoryResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True


# ── EXPENSE SCHEMAS
class ExpenseCreate(BaseModel):
    title: str
    amount: float = Field(gt=0)
    category_name: str  # Will resolve to category_id internally
    date: Union[date_type, None] = None

class ExpenseUpdate(BaseModel):
    title: Union[str, None] = None
    amount: Union[float, None] = Field(default=None, gt=0)
    category_name: Union[str, None] = None
    date: Union[date_type, None] = None

class ExpenseResponse(BaseModel):
    id: int
    title: str
    amount: float
    category_name: str
    date: Union[date_type, None] = None

    class Config:
        from_attributes = True