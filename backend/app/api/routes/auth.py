from fastapi import APIRouter

# ✅ IMPORT FROM AUTHENTICATION FILE
from app.core.authentication import fastapi_users, auth_backend

# ✅ SCHEMAS
from app.schemas.schemas import UserRead, UserCreate, UserUpdate

from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, delete

router = APIRouter()

# ── AUTH ROUTES ────────────────────────────────────────────────
router.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/jwt",
    tags=["auth"]
)


router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    tags=["auth"]
)

router.include_router(
    fastapi_users.get_reset_password_router(),
    tags=["auth"]
)

router.include_router(
    fastapi_users.get_verify_router(UserRead),
    tags=["auth"]
)

# USER ROUTES 
router.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"]
)