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


#CREATE EXPENSE 
from app.models.models import Category, Expense # Ensure these are imported

@router.post("")
async def create_expense(
    expense_in: ExpenseCreate,
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    try:
        # 1. Clean the category name (remove extra spaces)
        cat_name = expense_in.category_name.strip()

        # 2. Check if this category already exists for THIS user
        statement = select(Category).where(
            Category.name == cat_name,
            Category.user_id == user.id
        )
        result = await session.execute(statement)
        category = result.scalars().first()

        # 3. If it doesn't exist, create it on the fly!
        if not category:
            category = Category(name=cat_name, user_id=user.id)
            session.add(category)
            await session.flush() # This populates category.id without committing yet

        # 4. Create the expense using the ID we just found or created
        new_expense = Expense(
            title=expense_in.title,
            amount=expense_in.get_amount_in_subunits(), # Uses your schema helper!
            category_id=category.id,
            user_id=user.id,
            date=expense_in.date or datetime.now().date()
        )

        session.add(new_expense)
        await session.commit()
        await session.refresh(new_expense)
        
        return new_expense

    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))

# ── GET EXPENSES 
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


#UPDATE EXPENSE
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


#DELETE EXPENSE 
@router.delete("/{expense_id}")
async def delete_expense(
    expense_id: int, 
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user)
):
    # 1. Fetch the expense
    result = await session.execute(
        select(Expense).where(Expense.id == expense_id, Expense.user_id == user.id)
    )
    expense = result.scalar_one_or_none()

    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")

    # 2. Mark for deletion
    await session.delete(expense)
    
    # 3. SAVE THE CHANGE TO MYSQL (If you miss this, it won't delete!)
    await session.commit() 
    
    return {"message": "Deleted successfully"}

@router.delete("/categories/{category_id}")
async def delete_category(
    category_id: int, 
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user)
):
    statement = select(Category).where(Category.id == category_id, Category.user_id == user.id)
    result = await session.execute(statement)
    category = result.scalar_one_or_none()

    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    await session.delete(category)
    await session.commit()
    return {"message": "Category deleted. Linked expenses are now 'Uncategorized'."}