from typing import Optional
from fastapi import Depends, Request
from fastapi_users import BaseUserManager, FastAPIUsers, IntegerIDMixin
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users.db import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_async_session
from models import User

# ── CONFIG ─────────────────────────────────────────────────────
SECRET         = "changethis123secret999key"
TOKEN_LIFETIME = 60 * 60 * 24  # 24 hours in seconds


# ── USER DATABASE ──────────────────────────────────────────────
async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)


# ── USER MANAGER ──────────────────────────────────────────────
class UserManager(IntegerIDMixin, BaseUserManager[User, int]):
    reset_password_token_secret    = SECRET
    verification_token_secret      = SECRET

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
current_active_user          = fastapi_users.current_user(active=True)
current_active_verified_user = fastapi_users.current_user(active=True, verified=True)