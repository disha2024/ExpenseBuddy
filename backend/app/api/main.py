import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from database import create_db_and_tables

# Import your new routers
from api.routes import auth, profile, expenses, categories, pages

app = FastAPI(title="Expense Tracker API")

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

# 🌍 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 📁 Paths (Needed for mounting)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
frontend_path = os.path.abspath(os.path.join(BASE_DIR, "..", "frontend"))
UPLOAD_DIR = os.path.join(frontend_path, "uploads")

# 🔌 INCLUDE ROUTERS
app.include_router(auth.router, prefix="/auth")
app.include_router(profile.router)
app.include_router(expenses.router)
# app.include_router(categories.router) # If you create categories.py
app.include_router(pages.router)

# 📦 STATIC FILES
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
app.mount("/static", StaticFiles(directory=frontend_path), name="static")