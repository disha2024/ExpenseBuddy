import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete
from database import get_async_session
from models import User, Expense
from schemas import (
    UserRead, ProfileUpdate, PasswordChange, 
    CurrencyUpdate
)
from auth import current_active_user
from fastapi_users.password import PasswordHelper

router = APIRouter(prefix="/profile", tags=["profile"])

# Path for profile pictures (Relative to main.py's logic)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.abspath(os.path.join(BASE_DIR, "../../..", "frontend", "uploads"))

@router.get("", response_model=UserRead)
async def get_profile(current_user: User = Depends(current_active_user)):
    return current_user

@router.put("", response_model=UserRead)
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

@router.put("/password")
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

@router.put("/currency")
async def update_currency(
    data: CurrencyUpdate,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    current_user.currency = data.currency
    await session.commit()
    await session.refresh(current_user)
    return {"message": "Currency updated successfully"}

@router.post("/picture")
async def upload_picture(
    file: UploadFile = File(...),
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    filename = f"user_{current_user.id}.jpg"
    file_path = os.path.join(UPLOAD_DIR, filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    current_user.profile_picture = f"/uploads/{filename}"
    await session.commit()
    return {"picture_url": current_user.profile_picture}

@router.delete("/picture")
async def remove_profile_picture(
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    if not current_user.profile_picture:
        raise HTTPException(status_code=400, detail="No profile picture to remove")

    current_user.profile_picture = None
    await session.commit()
    await session.refresh(current_user)
    return {"message": "Profile picture removed successfully"}

@router.delete("/delete")
async def delete_account(
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    try:
        await session.execute(delete(Expense).where(Expense.user_id == current_user.id))
        await session.delete(current_user)
        await session.commit()
        return {"message": "Account deleted successfully"}
    except Exception:
        await session.rollback()
        raise HTTPException(status_code=500, detail="Could not delete account")