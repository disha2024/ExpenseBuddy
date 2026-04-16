from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List
from datetime import date
import traceback

from app.models.models import User, Expense, Category
from app.schemas.schemas import ExpenseCreate, ExpenseUpdate, ExpenseResponse
from app.core.authentication import current_active_user
from app.db.database import get_async_session

router = APIRouter(prefix="/expenses", tags=["expenses"])


# ── HELPER: GET OR CREATE CATEGORY ────────────────────────────
async def get_or_create_category(session: AsyncSession, name: str, user_id) -> Category | None:
    """
    MySQL-safe get-or-create. No savepoints. Commit-isolated insert.
    """
    # 1. Initial lookup
    result = await session.execute(
        select(Category).where(Category.name == name, Category.user_id == user_id)
    )
    category = result.scalar_one_or_none()
    print(f"🔍 Lookup '{name}' for user {user_id}: {'FOUND' if category else 'NOT FOUND'}")
    if category:
        return category

    # 2. Try inserting with isolated commit
    try:
        category = Category(name=name, user_id=user_id)
        session.add(category)
        await session.commit()
        await session.refresh(category)
        print(f"✅ Created category '{name}' for user {user_id} with id={category.id}")
        return category

    except Exception as e:
        print(f"⚠️ Insert failed (likely duplicate): {e}")
        await session.rollback()

    # 3. Re-query after rollback
    result = await session.execute(
        select(Category).where(Category.name == name, Category.user_id == user_id)
    )
    category = result.scalar_one_or_none()
    print(f"🔁 Re-query after rollback: {'FOUND' if category else 'STILL NOT FOUND ❌'}")
    return category


# ── CREATE EXPENSE ─────────────────────────────────────────────
@router.post("", response_model=ExpenseResponse)
async def create_expense(
    expense: ExpenseCreate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user)
):
    user_id = current_user.id
    clean_name = expense.category_name.strip().lower()

    try:
        category = await get_or_create_category(session, clean_name, user_id)

        if not category:
            raise HTTPException(status_code=500, detail="Category could not be retrieved or created.")

        # Capture plain values before any further awaits
        category_id = category.id
        category_name = category.name

        new_expense = Expense(
            title=expense.title,
            amount=expense.amount,
            category_id=category_id,
            date=expense.date if expense.date else date.today(),
            user_id=user_id
        )

        session.add(new_expense)
        await session.commit()
        await session.refresh(new_expense)

        return ExpenseResponse(
            id=new_expense.id,
            title=new_expense.title,
            amount=new_expense.amount,
            category_name=category_name,
            date=new_expense.date
        )

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        print(f"❌ Error in create_expense: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


# ── GET EXPENSES ───────────────────────────────────────────────
@router.get("", response_model=List[ExpenseResponse])
async def get_expenses(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user)
):
    try:
        result = await session.execute(
            select(Expense, Category)
            .join(Category, Expense.category_id == Category.id)
            .where(Expense.user_id == current_user.id)
            .order_by(Expense.date.desc())
        )
        rows = result.all()

        return [
            ExpenseResponse(
                id=exp.id,
                title=exp.title,
                amount=exp.amount,
                category_name=cat.name,
                date=exp.date
            ) for exp, cat in rows
        ]

    except Exception as e:
        print(f"❌ Error in get_expenses: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error fetching expenses: {str(e)}")


# ── UPDATE EXPENSE ─────────────────────────────────────────────
@router.put("/{expense_id}", response_model=ExpenseResponse)
async def update_expense(
    expense_id: int,
    expense_data: ExpenseUpdate,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user)
):
    try:
        result = await session.execute(
            select(Expense).where(
                Expense.id == expense_id,
                Expense.user_id == current_user.id
            )
        )
        expense = result.scalar_one_or_none()

        if not expense:
            raise HTTPException(status_code=404, detail="Expense not found")

        if expense_data.title is not None:
            expense.title = expense_data.title
        if expense_data.amount is not None:
            expense.amount = expense_data.amount
        if expense_data.date is not None:
            expense.date = expense_data.date

        # Update category if provided
        if expense_data.category_name is not None:
            clean_name = expense_data.category_name.strip().lower()
            category = await get_or_create_category(session, clean_name, current_user.id)

            if not category:
                raise HTTPException(status_code=500, detail="Category could not be retrieved or created.")

            expense.category_id = category.id

        await session.commit()

        # Re-fetch with joined category for the response
        final_result = await session.execute(
            select(Expense, Category)
            .join(Category, Expense.category_id == Category.id)
            .where(Expense.id == expense_id)
        )
        row = final_result.first()

        if not row:
            raise HTTPException(status_code=404, detail="Expense not found after update")

        exp, cat = row

        return ExpenseResponse(
            id=exp.id,
            title=exp.title,
            amount=exp.amount,
            category_name=cat.name,
            date=exp.date
        )

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        print(f"❌ Error in update_expense: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")


# ── DELETE EXPENSE ─────────────────────────────────────────────
@router.delete("/{expense_id}")
async def delete_expense(
    expense_id: int,
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user)
):
    try:
        result = await session.execute(
            select(Expense).where(
                Expense.id == expense_id,
                Expense.user_id == current_user.id
            )
        )
        expense = result.scalar_one_or_none()

        if not expense:
            raise HTTPException(status_code=404, detail="Expense not found")

        await session.delete(expense)
        await session.commit()

        return {"message": "Expense deleted"}

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        print(f"❌ Error in delete_expense: {str(e)}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")