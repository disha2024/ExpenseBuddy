import os
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from typing import List
from datetime import date
from database import Base 
from database import engine, get_db
from models import Base, Expense, User
from schemas import ExpenseCreate, ExpenseUpdate, ExpenseResponse, UserCreate, UserResponse, Token
from auth import hash_password, verify_password, create_access_token, get_current_user

# APP INITIALIZATION
app = FastAPI(title="Expense Tracker API")

Base.metadata.create_all(bind=engine)  # Create tables if they don't exist

# CORS CONFIG
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# STATIC FILES
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
frontend_path = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend"))

if not os.path.exists(frontend_path):
    raise RuntimeError(f"Frontend directory not found at {frontend_path}")

# SERVE FRONTEND FILES (Must be at the end after all API routes)
@app.get("/")
def serve_index():
    return FileResponse(os.path.join(frontend_path, "index.html"), media_type="text/html")

# Mount static files for CSS, JS, etc.
app.mount("/static", StaticFiles(directory=frontend_path), name="static")



# REGISTER
@app.post("/register", response_model=UserResponse)
def register(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == user.username).first():
        raise HTTPException(status_code=400, detail="Username already exists")
    
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email already exists")

    new_user = User(
        username=user.username,
        email=user.email,
        password=hash_password(user.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


# LOGIN
@app.post("/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_access_token(data={"sub": user.username})
    return {"access_token": token, "token_type": "bearer"}


# CREATE EXPENSE
@app.post("/expenses", response_model=ExpenseResponse)
def create_expense(
    expense: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    new_expense = Expense(
        title=expense.title,
        amount=expense.amount,
        category=expense.category,
        date=expense.date if expense.date else date.today(),
        user_id=current_user.id
    )
    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)
    return new_expense


# GET ALL EXPENSES
@app.get("/expenses", response_model=List[ExpenseResponse])
def get_expenses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Expense).filter(Expense.user_id == current_user.id).all()


# DELETE EXPENSE
@app.delete("/expenses/{expense_id}")
def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
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


# UPDATE EXPENSE
@app.put("/expenses/{expense_id}", response_model=ExpenseResponse)
def update_expense(
    expense_id: int,
    updated: ExpenseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.user_id == current_user.id
    ).first()

    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    if updated.title is not None:
        expense.title = updated.title
    if updated.amount is not None:
        expense.amount = updated.amount
    if updated.category is not None:
        expense.category = updated.category
    if updated.date is not None:
        expense.date = updated.date

    db.commit()
    db.refresh(expense)
    return expense