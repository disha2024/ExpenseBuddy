from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from datetime import date
from database import get_db
from models import User, Expense, Category
from schemas import ExpenseCreate, ExpenseUpdate, ExpenseResponse
from auth import current_active_user

router = APIRouter(prefix="/expenses", tags=["expenses"])

@router.post("", response_model=ExpenseResponse)
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

    return ExpenseResponse(
        id=new_expense.id,
        title=new_expense.title,
        amount=new_expense.amount,
        category_name=category.name,
        date=new_expense.date
    )

@router.get("", response_model=List[ExpenseResponse])
def get_expenses(
    db: Session = Depends(get_db),
    current_user: User = Depends(current_active_user)
):
    expenses = db.query(Expense).filter(
        Expense.user_id == current_user.id
    ).all()
    
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

@router.put("/{expense_id}", response_model=ExpenseResponse)
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
    if expense_data.date is not None:
        expense.date = expense_data.date
        
    if expense_data.category_name is not None:
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

    db.commit()
    db.refresh(expense)
    
    # Refresh category name for response
    cat = db.query(Category).filter(Category.id == expense.category_id).first()
    return ExpenseResponse(
        id=expense.id,
        title=expense.title,
        amount=expense.amount,
        category_name=cat.name if cat else "Unknown",
        date=expense.date
    )

@router.delete("/{expense_id}")
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
    return {"message": "Expense deleted"}