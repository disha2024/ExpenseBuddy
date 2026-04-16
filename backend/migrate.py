#!/usr/bin/env python
"""Reset database and recreate tables with new schema"""

from sqlalchemy import create_engine, text
from sqlmodel import SQLModel
from app.models.models import User, Expense, Category

DATABASE_URL = "mysql+pymysql://root:dishasql%402004@localhost:3306/expense_db"

def reset_database():
    engine = create_engine(DATABASE_URL)
    
    # Drop old tables with foreign key checks disabled
    with engine.connect() as conn:
        try:
            conn.execute(text('SET FOREIGN_KEY_CHECKS=0'))
            conn.execute(text('DROP TABLE IF EXISTS expense'))
            conn.execute(text('DROP TABLE IF EXISTS category'))
            conn.execute(text('DROP TABLE IF EXISTS users'))
            conn.execute(text('SET FOREIGN_KEY_CHECKS=1'))
            conn.commit()
            print("✅ Old tables dropped successfully")
        except Exception as e:
            print(f"❌ Error dropping tables: {e}")
            conn.rollback()
    
    # Create new tables
    try:
        SQLModel.metadata.create_all(engine)
        print("✅ New tables created successfully")
    except Exception as e:
        print(f"❌ Error creating tables: {e}")

if __name__ == "__main__":
    reset_database()
