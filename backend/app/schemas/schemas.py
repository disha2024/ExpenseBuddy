from fastapi_users import schemas as fu_schemas
from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import date as date_type, datetime
from typing import Optional, Union, Any
from enum import Enum

# ── ENUMS
class CurrencyEnum(str, Enum):
    USD = "USD"
    EUR = "EUR"
    GBP = "GBP"
    INR = "INR"

# ── USER SCHEMAS (FastAPI Users)
class UserRead(fu_schemas.BaseUser[int]):
    username: str
    joined_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    profile_picture: Optional[str] = None
    currency: CurrencyEnum = CurrencyEnum.USD
    
    model_config = ConfigDict(from_attributes=True)

class UserCreate(fu_schemas.BaseUserCreate):
    username: str
    currency: Optional[CurrencyEnum] = CurrencyEnum.INR

class UserUpdate(fu_schemas.BaseUserUpdate):
    username: Optional[str] = None
    profile_picture: Optional[str] = None
    currency: Optional[CurrencyEnum] = None


# ── TOKEN & AUTH SCHEMAS
class Token(BaseModel):
    access_token: str
    token_type: str

class ProfileUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

class CurrencyUpdate(BaseModel):
    currency: CurrencyEnum


# ── CATEGORY SCHEMAS
class CategoryCreate(BaseModel):
    name: str

class CategoryResponse(BaseModel):
    id: int
    name: str

    model_config = ConfigDict(from_attributes=True)


# ── EXPENSE SCHEMAS

class ExpenseBase(BaseModel):
    title: str
    category_name: str  # Frontend sends "Food", "Rent", etc.
    date: Optional[date_type] = None

class ExpenseCreate(ExpenseBase):
    # We take a float from the user (e.g., 10.50)
    amount: float = Field(gt=0, description="Enter amount in decimal (e.g., 10.50)")

    def get_amount_in_subunits(self) -> int:
        """
        Converts the float input to an integer (Paise/Cents).
        10.50 -> 1050
        """
        return int(round(self.amount * 100))

class ExpenseUpdate(BaseModel):
    title: Optional[str] = None
    amount: Optional[float] = Field(default=None, gt=0)
    category_name: Optional[str] = None
    date: Optional[date_type] = None

    def get_amount_in_subunits(self) -> Optional[int]:
        if self.amount is None:
            return None
        return int(round(self.amount * 100))

class ExpenseResponse(BaseModel):
    id: int
    title: str
    amount: float  # Displayed as float (10.50)
    category_name: str # Returned as the name of the category
    date: date_type

    @field_validator("amount", mode="before")
    @classmethod
    def convert_from_subunits(cls, v: Any) -> float:
        """
        Converts DB integer (1050) back to float (10.50) for the UI.
        """
        if isinstance(v, int):
            return v / 100
        return v

    model_config = ConfigDict(from_attributes=True)