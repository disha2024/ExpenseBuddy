import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.api.routes import auth, profile, expenses, categories
from app.db.database import create_db_and_tables

app = FastAPI(title="Expense Tracker API")

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/")
def read_root():
    index_path = os.path.abspath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "frontend", "index.html")
    )
    return FileResponse(index_path)

@app.get("/dashboard.html")
def serve_dashboard():
    dashboard_path = os.path.abspath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "frontend", "dashboard.html")
    )
    return FileResponse(dashboard_path)

@app.get("/profile.html")
def serve_profile():
    profile_path = os.path.abspath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "frontend", "profile.html")
    )
    return FileResponse(profile_path)

@app.get("/reset-password.html")
def serve_reset_password():
    reset_path = os.path.abspath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "frontend", "reset_password.html")
    )
    return FileResponse(reset_path)

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
# Navigate from backend/app/api/main.py to root, then to frontend
frontend_path = os.path.abspath(os.path.join(BASE_DIR, "..", "..", "..", "frontend"))
UPLOAD_DIR = os.path.join(frontend_path, "uploads")

# Create uploads directory if it doesn't exist
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 🔌 INCLUDE ROUTERS
app.include_router(auth.router, prefix="/auth")
app.include_router(profile.router)
app.include_router(expenses.router)
app.include_router(categories.router)
# app.include_router(pages.router)

# 📦 STATIC FILES
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
app.mount("/static", StaticFiles(directory=frontend_path), name="static")