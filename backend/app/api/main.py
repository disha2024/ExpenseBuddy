import os
import shutil
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy import delete
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from datetime import date

from database import create_db_and_tables, get_db, get_async_session
from models import User, Expense, Category
from schemas import (
    UserRead, UserCreate, UserUpdate,
    ExpenseCreate, ExpenseUpdate, ExpenseResponse,
    CategoryCreate, CategoryResponse,
    ProfileUpdate, CurrencyUpdate, PasswordChange
)
from auth import fastapi_users, auth_backend, current_active_user
from fastapi_users.password import PasswordHelper


# 🚀 APP
app = FastAPI(title="Expense Tracker API")


#FIXED STARTUP EVENT
@app.on_event("startup")
def on_startup():
    create_db_and_tables()


# 🌍 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 📁 Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
frontend_path = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend"))
UPLOAD_DIR = os.path.join(frontend_path, "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


# 🔐 AUTH ROUTES
app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"]
)

app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"]
)

app.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"]
)

app.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth",
    tags=["auth"]
)

app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"]
)


# 🌐 SERVE PAGES
@app.get("/")
def serve_index():
    return FileResponse(os.path.join(frontend_path, "index.html"))

@app.get("/dashboard.html")
def serve_dashboard():
    return FileResponse(os.path.join(frontend_path, "dashboard.html"))

@app.get("/profile.html")
def serve_profile_page():
    return FileResponse(os.path.join(frontend_path, "profile.html"))

@app.get("/reset-password.html")
def serve_reset():
    return FileResponse(os.path.join(frontend_path, "reset-password.html"))


# 👤 PROFILE
@app.get("/profile", response_model=UserRead)
async def get_profile(current_user: User = Depends(current_active_user)):
    return current_user


@app.put("/profile", response_model=UserRead)
async def update_profile(
    data: ProfileUpdate,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    if data.username:
        current_user.username = data.username
    if data.email:
        current_user.email = data.email

    await session.commit()
    await session.refresh(current_user)
    return current_user


@app.put("/profile/password")
async def change_password(
    data: PasswordChange,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    pwd_helper = PasswordHelper()
    verified, _ = pwd_helper.verify_and_update(
        data.current_password,
        current_user.hashed_password
    )

    if not verified:
        raise HTTPException(status_code=401, detail="Incorrect password")

    current_user.hashed_password = pwd_helper.hash(data.new_password)
    await session.commit()

    return {"message": "Password changed successfully"}


@app.put("/profile/currency")
async def update_currency(
    data: CurrencyUpdate,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    current_user.currency = data.currency
    await session.commit()
    await session.refresh(current_user)
    return {"message": "Currency updated successfully"}


@app.post("/profile/picture")
async def upload_picture(
    file: UploadFile = File(...),
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    filename = f"user_{current_user.id}.jpg"
    file_path = os.path.join(UPLOAD_DIR, filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    current_user.profile_picture = f"/uploads/{filename}"
    await session.commit()

    return {"picture_url": current_user.profile_picture}


@app.delete("/profile/picture")
async def remove_profile_picture(
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    # Check if user even has a custom picture
    if not current_user.profile_picture:
        raise HTTPException(status_code=400, detail="No profile picture to remove")

    # Optional: Delete the actual file from the 'uploads' folder
    # file_path = os.path.join(UPLOAD_DIR, f"user_{current_user.id}.jpg")
    # if os.path.exists(file_path):
    #     os.remove(file_path)

    # Reset the field in the database
    current_user.profile_picture = None
    await session.commit()
    await session.refresh(current_user)

    return {"message": "Profile picture removed successfully"}

#profile delete
@app.delete("/profile/delete")
async def delete_account(
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    try:
        # Delete all expenses for the user first
        await session.execute(delete(Expense).where(Expense.user_id == current_user.id))
        # Then delete the user
        await session.delete(current_user)
        await session.commit()
        return {"message": "Account deleted successfully"}
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail="Could not delete account")


# � CATEGORIES
@app.post("/categories", response_model=CategoryResponse)
def create_category(
    category: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(current_active_user)
):
    # Check if category already exists for this user
    existing = db.query(Category).filter(
        Category.name == category.name,
        Category.user_id == current_user.id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Category already exists")

    new_category = Category(name=category.name, user_id=current_user.id)
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category


@app.get("/categories", response_model=List[CategoryResponse])
def get_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(current_active_user)
):
    return db.query(Category).filter(Category.user_id == current_user.id).all()


# �💰 EXPENSES
@app.post("/expenses", response_model=ExpenseResponse)
def create_expense(
    expense: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(current_active_user)
):
    # Get or create category
    category = db.query(Category).filter(
        Category.name == expense.category_name,
        Category.user_id == current_user.id
    ).first()
    if not category:
        category = Category(name=expense.category_name, user_id=current_user.id)
        db.add(category)
        db.commit()
        db.refresh(category)

    new_expense = Expense(
        title=expense.title,
        amount=expense.amount,
        category_id=category.id,
        date=expense.date if expense.date else date.today(),
        user_id=current_user.id
    )

    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)

    # Return with category_name
    return ExpenseResponse(
        id=new_expense.id,
        title=new_expense.title,
        amount=new_expense.amount,
        category_name=category.name,
        date=new_expense.date
    )


@app.get("/expenses", response_model=List[ExpenseResponse])
def get_expenses(
    db: Session = Depends(get_db),
    current_user: User = Depends(current_active_user)
):
    expenses = db.query(Expense).filter(
        Expense.user_id == current_user.id
    ).all()
    
    # Build response with category names
    result = []
    for exp in expenses:
        category = db.query(Category).filter(Category.id == exp.category_id).first()
        result.append(ExpenseResponse(
            id=exp.id,
            title=exp.title,
            amount=exp.amount,
            category_name=category.name if category else "Unknown",
            date=exp.date
        ))
    return result


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
        raise HTTPException(status_code=404, detail="Not found")

    db.delete(expense)
    db.commit()

@app.put("/expenses/{expense_id}", response_model=ExpenseResponse)
def update_expense(
    expense_id: int,
    expense_data: ExpenseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(current_active_user)
):
    expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.user_id == current_user.id
    ).first()

    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    if expense_data.title is not None:
        expense.title = expense_data.title
    if expense_data.amount is not None:
        expense.amount = expense_data.amount
    if expense_data.category_name is not None:
        # Get or create category
        category = db.query(Category).filter(
            Category.name == expense_data.category_name,
            Category.user_id == current_user.id
        ).first()
        if not category:
            category = Category(name=expense_data.category_name, user_id=current_user.id)
            db.add(category)
            db.commit()
            db.refresh(category)
        expense.category_id = category.id
    if expense_data.date is not None:
        expense.date = expense_data.date

    db.commit()
    db.refresh(expense)
    
    # Return with category_name
    category = db.query(Category).filter(Category.id == expense.category_id).first()
    return ExpenseResponse(
        id=expense.id,
        title=expense.title,
        amount=expense.amount,
        category_name=category.name if category else "Unknown",
        date=expense.date
    )


# 📦 STATIC FILES
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
app.mount("/static", StaticFiles(directory=frontend_path), name="static")