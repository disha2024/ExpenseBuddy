from sqlmodel import create_engine, Session, SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker # Added for more robust session management
from typing import AsyncGenerator
import asyncio

# Note: Ensure all models are imported before SQLModel.metadata.create_all is called
from app.models.models import User, Expense, Category

DATABASE_URL = "mysql+pymysql://root:dishasql%402004@localhost:3306/expense_db"
DATABASE_URL_ASYNC = "mysql+aiomysql://root:dishasql%402004@localhost:3306/expense_db"

# Synchronous engine for table creation and migrations
engine = create_engine(DATABASE_URL, echo=False)

# Asynchronous engine for the FastAPI app
async_engine = create_async_engine(DATABASE_URL_ASYNC, echo=False)

# This replaces the metadata creation logic to ensure SQLModel tables are picked up
def create_db_and_tables():
    """
    Creates all tables in the database. 
    Call this during app startup.
    """
    SQLModel.metadata.create_all(engine)

def get_db():
    """Sync session generator (useful for scripts or non-async routes)"""
    with Session(engine) as session:
        yield session

async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Async session generator used by FastAPI Routes and FastAPI Users.
    We use sessionmaker to ensure the session is properly bound to the async engine.
    """
    async_session_maker = sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session_maker() as session:
        yield session