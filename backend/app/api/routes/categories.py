from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import List

from app.models.models import Category, User
from app.schemas.schemas import CategoryResponse
from app.core.authentication import current_active_user
from app.db.database import get_async_session

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=List[CategoryResponse])
async def get_categories(
    session: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user)
):
    try:
        result = await session.execute(
            select(Category).where(Category.user_id == current_user.id)
        )
        categories = result.scalars().all()
        return categories

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching categories: {str(e)}")
    
