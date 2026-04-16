from typing import Optional
from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers, IntegerIDMixin
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlmodel.ext.asyncio.session import AsyncSession

# ✅ FIXED IMPORTS
from app.db.database import get_async_session
from app.models.models import User


# ── CONFIG ─────────────────────────────────────────────────────
SECRET = "changethis123secret999keyforjwt256bitsminimumlength"
TOKEN_LIFETIME = 60 * 60 * 24  # 24 hours


# ── USER DATABASE ──────────────────────────────────────────────
async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)


# ── USER MANAGER ──────────────────────────────────────────────
class UserManager(IntegerIDMixin, BaseUserManager[User, int]):
    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def create(self, user_create, safe: bool = False, request: Optional[Request] = None):
        if not hasattr(user_create, 'currency') or user_create.currency is None:
            user_create.currency = "INR"
        return await super().create(user_create, safe=safe, request=request)

    async def on_after_register(self, user: User, request: Optional[Request] = None):
        print(f"✅ New user registered: {user.email}")

    async def on_after_forgot_password(self, user: User, token: str, request: Optional[Request] = None):
        print(f"📧 Password reset token for {user.email}: {token}")

    async def on_after_request_verify(self, user: User, token: str, request: Optional[Request] = None):
        print(f"📧 Verification token for {user.email}: {token}")


async def get_user_manager(user_db=Depends(get_user_db)):
    yield UserManager(user_db)


# ── JWT AUTH BACKEND ───────────────────────────────────────────
bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=SECRET, lifetime_seconds=TOKEN_LIFETIME)


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)


# ── FASTAPI USERS INSTANCE ─────────────────────────────────────
fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend],
)


# ── CURRENT USER HELPERS ───────────────────────────────────────
current_active_user = fastapi_users.current_user(active=True)
current_active_verified_user = fastapi_users.current_user(active=True, verified=True)