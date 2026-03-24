import os
import shutil
import time
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import date
from database import Base, engine, get_db, async_engine, get_async_session
from models import User, Expense
from schemas import (
    UserRead, UserCreate, UserUpdate,
    ExpenseCreate, ExpenseUpdate, ExpenseResponse,
    ProfileUpdate, CurrencyUpdate, PasswordChange
)
from auth import fastapi_users, auth_backend, current_active_user
from fastapi_users.db import SQLAlchemyUserDatabase
from fastapi_users.password import PasswordHelper

#  APP
app = FastAPI(title="Expense Tracker API")

# CREATE TABLES
@app.on_event("startup")
async def startup():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# CORS 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#Paths
BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
frontend_path = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend"))
UPLOAD_DIR    = os.path.join(frontend_path, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# ── AUTH ROUTES (FastAPI Users) ────────────────────────────────
# POST /auth/jwt/login       → Login, returns JWT token
# POST /auth/jwt/logout      → Logout
app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"]
)

# POST /auth/register        → Register new user
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"]
)

# POST /auth/forgot-password → Send reset email
# POST /auth/reset-password  → Reset password with token
app.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"]
)

# POST /auth/request-verify-token → Send verification email
# POST /auth/verify               → Verify email
app.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth",
    tags=["auth"]
)

# GET  /users/me             → Get current user profile
# PATCH /users/me            → Update profile
app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"]
)


# ── SERVE PAGES 
@app.get("/")
def serve_index():
    return FileResponse(os.path.join(frontend_path, "index.html"), media_type="text/html")

@app.get("/dashboard.html")
def serve_dashboard():
    return FileResponse(os.path.join(frontend_path, "dashboard.html"), media_type="text/html")

@app.get("/profile.html")
def serve_profile_page():
    return FileResponse(os.path.join(frontend_path, "profile.html"), media_type="text/html")

@app.get("/reset-password.html")
def serve_reset():
    return FileResponse(os.path.join(frontend_path, "reset-password.html"), media_type="text/html")


# PROFILE — GET 
@app.get("/profile", response_model=UserRead)
async def get_profile(current_user: User = Depends(current_active_user)):
    return current_user


# PROFILE — UPDATE USERNAME & EMAIL 
@app.put("/profile", response_model=UserRead)
async def update_profile(
    data: ProfileUpdate,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    if data.username and data.username != current_user.username:
        current_user.username = data.username
    if data.email and data.email != current_user.email:
        current_user.email = data.email
    await session.commit()
    await session.refresh(current_user)
    return current_user


# ── PROFILE — CHANGE PASSWORD
@app.put("/profile/password")
async def change_password(
    data: PasswordChange,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    pwd_helper = PasswordHelper()
    verified, _ = pwd_helper.verify_and_update(data.current_password, current_user.hashed_password)
    if not verified:
        raise HTTPException(status_code=401, detail="Current password is incorrect")
    if len(data.new_password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")
    current_user.hashed_password = pwd_helper.hash(data.new_password)
    await session.commit()
    return {"message": "Password changed successfully"}


# ── PROFILE — UPLOAD PICTURE
@app.post("/profile/picture")
async def upload_picture(
    file: UploadFile = File(...),
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    allowed = ["image/jpeg", "image/png", "image/jpg", "image/webp"]
    if file.content_type not in allowed:
        raise HTTPException(status_code=400, detail="Only JPEG, PNG and WebP images are allowed")
    ext       = file.filename.split(".")[-1]
    filename  = f"user_{current_user.id}.{ext}"
    file_path = os.path.join(UPLOAD_DIR, filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    current_user.profile_picture = f"/uploads/{filename}"
    await session.commit()
    return {"picture_url": current_user.profile_picture}


# ── PROFILE — REMOVE PICTURE 
@app.delete("/profile/picture")
async def remove_picture(
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    if current_user.profile_picture:
        file_path = os.path.join(UPLOAD_DIR, os.path.basename(current_user.profile_picture.split("?")[0]))
        if os.path.exists(file_path):
            os.remove(file_path)
    current_user.profile_picture = None
    await session.commit()
    return {"message": "Profile picture removed successfully"}


# ── PROFILE — CURRENCY 
@app.put("/profile/currency")
async def update_currency(
    data: CurrencyUpdate,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    allowed = ["₹", "$", "€", "£", "¥"]
    if data.currency not in allowed:
        raise HTTPException(status_code=400, detail="Invalid currency")
    current_user.currency = data.currency
    await session.commit()
    return {"message": "Currency updated", "currency": current_user.currency}


# EXPENSES — CREATE
@app.post("/expenses", response_model=ExpenseResponse)
def create_expense(
    expense: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(current_active_user)
):
    new_expense = Expense(
        title=expense.title, amount=expense.amount,
        category=expense.category,
        date=expense.date if expense.date else date.today(),
        user_id=current_user.id
    )
    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)
    return new_expense


# EXPENSES — GET ALL
@app.get("/expenses", response_model=List[ExpenseResponse])
def get_expenses(
    db: Session = Depends(get_db),
    current_user: User = Depends(current_active_user)
):
    return db.query(Expense).filter(Expense.user_id == current_user.id).all()


# EXPENSES UPDATE 
@app.put("/expenses/{expense_id}", response_model=ExpenseResponse)
def update_expense(
    expense_id: int,
    updated: ExpenseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(current_active_user)
):
    expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.user_id == current_user.id
    ).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    if updated.title    is not None: expense.title    = updated.title
    if updated.amount   is not None: expense.amount   = updated.amount
    if updated.category is not None: expense.category = updated.category
    if updated.date     is not None: expense.date     = updated.date
    db.commit()
    db.refresh(expense)
    return expense


# EXPENSES — DELETE
@app.delete("/expenses/{expense_id}")
def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(current_active_user)
):
    expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.user_id == current_user.id
    ).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    db.delete(expense)
    db.commit()
    return {"message": "Expense deleted successfully"}


# ── STATIC FILES — must be last ───────────────────────────────
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR),    name="uploads")
app.mount("/static",  StaticFiles(directory=frontend_path), name="static")