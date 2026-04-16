import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlmodel import select, delete
from sqlmodel.ext.asyncio.session import AsyncSession

from app.db.database import get_async_session
from app.models.models import User, Expense
from app.schemas.schemas import (
    UserRead, ProfileUpdate, PasswordChange, CurrencyUpdate
)
from app.core.authentication import current_active_user
from fastapi_users.password import PasswordHelper

router = APIRouter(prefix="/profile", tags=["profile"])

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_DIR = os.path.abspath(
    os.path.join(BASE_DIR, "../../..", "frontend", "uploads")
)


# ── GET PROFILE ────────────────────────────────────────────────
@router.get("", response_model=UserRead)
async def get_profile(current_user: User = Depends(current_active_user)):
    return current_user


# ── UPDATE PROFILE ─────────────────────────────────────────────
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


# ── CHANGE PASSWORD ────────────────────────────────────────────
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


# ── UPDATE CURRENCY ────────────────────────────────────────────
@router.put("/currency")
async def update_currency(
    data: CurrencyUpdate,
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    try:
        current_user.currency = data.currency

        await session.commit()
        await session.refresh(current_user)

        return {"message": "Currency updated successfully"}

    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Error updating currency: {str(e)}")


# ── UPLOAD PROFILE PICTURE ─────────────────────────────────────
@router.post("/picture")
async def upload_picture(
    file: UploadFile = File(...),
    current_user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    try:
        os.makedirs(UPLOAD_DIR, exist_ok=True)

        filename = f"user_{current_user.id}.jpg"
        file_path = os.path.join(UPLOAD_DIR, filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        current_user.profile_picture = f"/uploads/{filename}"

        await session.commit()

        return {"picture_url": current_user.profile_picture}

    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Error uploading picture: {str(e)}")


# ── REMOVE PROFILE PICTURE ─────────────────────────────────────
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