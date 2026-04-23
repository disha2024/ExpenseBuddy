import os
import shutil
from fastapi import UploadFile, File
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlmodel import select, delete
from sqlmodel.ext.asyncio.session import AsyncSession
from app.db.database import get_db
from sqlmodel import Session

from app.db.database import get_async_session
from app.models.models import User, Expense
from app.schemas.schemas import (
    UserRead, ProfileUpdate, PasswordChange, CurrencyUpdate,ProfileUpdate
)

from app.core.authentication import current_active_user
from fastapi_users.password import PasswordHelper

router = APIRouter(prefix="/profile", tags=["profile"])

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.abspath(
    os.path.join(BASE_DIR, "../../..", "frontend", "uploads")
)



# GET PROFILE
@router.get("", response_model=UserRead)
async def get_profile(current_user: User = Depends(current_active_user)):
    return current_user


#UPDATE PROFILE
@router.put("", response_model=UserRead)
async def update_profile(
    data: ProfileUpdate,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    try:
        if data.username:
            current_user.username = data.username
        if data.email:
            current_user.email = data.email

        await session.commit()
        await session.refresh(current_user)
        return current_user

    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating profile: {str(e)}")


#  CHANGE PASSWORD
@router.put("/password")
async def change_password(
    data: PasswordChange,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    try:
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

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Error changing password: {str(e)}")


# UPDATE CURRENCY 
from app.models.models import Expense
from sqlalchemy import select, func

@router.put("/currency")
async def update_currency(
    new_currency: str, 
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    # 1. Check if user has any expenses
    expense_check = await session.execute(
        select(func.count(Expense.id)).where(Expense.user_id == user.id)
    )
    count = expense_check.scalar()

    if count > 0:
        raise HTTPException(
            status_code=400, 
            detail="Cannot change currency after expenses have been recorded. Delete all expenses first."
        )

    # 2. Update if no expenses found
    user.currency = new_currency
    session.add(user)
    await session.commit()
    
    return {"message": "Currency updated successfully", "currency": new_currency}


# UPLOAD PROFILE PICTURE 
@router.post("/picture")
async def upload_picture(
    file: UploadFile = File(...), 
    user=Depends(current_active_user),
    session=Depends(get_async_session)
):
    # 1. Create uploads folder if it doesn't exist
    os.makedirs("uploads", exist_ok=True)
    
    # 2. Create a unique filename for the user
    file_path = f"uploads/user_{user.id}.jpg"
    
    # 3. Save the ACTUAL file content (from any folder the user chose)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # 4. Update the user record in the DB with the new path
    user.profile_picture = f"/{file_path}"
    session.add(user)
    await session.commit()
    
    return {"message": "Success", "path": user.profile_picture}

#  REMOVE PROFILE PICTURE
@router.delete("/picture")
async def remove_profile_picture(
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    try:
        if not current_user.profile_picture:
            raise HTTPException(status_code=400, detail="No profile picture to remove")

        current_user.profile_picture = None

        await session.commit()
        await session.refresh(current_user)

        return {"message": "Profile picture removed successfully"}

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Error removing picture: {str(e)}")


#profile update
@router.put("/profile")
async def update_profile(
    profile_data: ProfileUpdate, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(current_active_user)
):
    # Check if currency is being changed
    if profile_data.currency and profile_data.currency != current_user.currency:
        # Check for existing expenses
        expense_count = db.query(Expense).filter(Expense.user_id == current_user.id).count()
        
        if expense_count > 0:
            raise HTTPException(
                status_code=400, 
                detail="Cannot change currency after expenses have been recorded. Delete all expenses to change currency."
            )
        
        current_user.currency = profile_data.currency

    # Continue with other updates (username, email, etc.)
    current_user.username = profile_data.username
    current_user.email = profile_data.email
    
    db.commit()
    return {"message": "Profile updated successfully"}

# ── DELETE ACCOUNT ─────────────────────────────────────────────
@router.delete("/delete")
async def delete_account(
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    try:
        await session.execute(
            delete(Expense).where(Expense.user_id == current_user.id)
        )

        await session.delete(current_user)
        await session.commit()

        return {"message": "Account deleted successfully"}

    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Could not delete account: {str(e)}")