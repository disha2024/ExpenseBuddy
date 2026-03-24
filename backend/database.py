from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from typing import AsyncGenerator

# ── SYNC (for regular routes) ──────────────────────────────────
DATABASE_URL       = "mysql+pymysql://root:dishasql%402004@localhost:3306/expense_db"
# ── ASYNC (required by FastAPI Users) ─────────────────────────
DATABASE_URL_ASYNC = "mysql+aiomysql://root:dishasql%402004@localhost:3306/expense_db"

# Sync engine — used by expense routes
engine       = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base         = declarative_base()

# Async engine — used by FastAPI Users
async_engine         = create_async_engine(DATABASE_URL_ASYNC)
AsyncSessionLocal    = sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

# ── SYNC DEPENDENCY ────────────────────────────────────────────
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ── ASYNC DEPENDENCY (for FastAPI Users) ──────────────────────
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session