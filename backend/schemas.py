from pydantic import BaseModel, Field
from datetime import date as date_type
from typing import Union


# USER SCHEMAS
class UserCreate(BaseModel):
    username: str
    email: str
    password: str

class UserResponse(BaseModel):
    id: int
    username: str
    email: str

    model_config = {"from_attributes": True}

class Token(BaseModel):
    access_token: str
    token_type: str


# EXPENSE SCHEMAS
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

    model_config = {"from_attributes": True}