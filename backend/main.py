from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from datetime import date

app = FastAPI()

# ✅ Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage
expenses = []
current_id = 1


# ✅ Pydantic Model (WITH CATEGORY)
class Expense(BaseModel):
    title: str
    amount: float
    category: str
    date: date


# ✅ Add Expense
@app.post("/expenses")
def add_expense(expense: Expense):
    global current_id

    new_expense = {
        "id": current_id,
        "title": expense.title,
        "amount": expense.amount,
        "category": expense.category,
        "date": expense.date
    }

    expenses.append(new_expense)
    current_id += 1

    return {"message": "Expense added successfully", "data": new_expense}


# ✅ Get All Expenses
@app.get("/expenses")
def get_all_expenses():
    return expenses


# ✅ Update Expense
@app.put("/expenses/{expense_id}")
def update_expense(expense_id: int, updated_expense: Expense):

    for expense in expenses:
        if expense["id"] == expense_id:
            expense["title"] = updated_expense.title
            expense["amount"] = updated_expense.amount
            expense["category"] = updated_expense.category
            expense["date"] = updated_expense.date
            return {"message": "Expense updated successfully", "data": expense}

    raise HTTPException(status_code=404, detail="Expense not found")


# ✅ Delete Expense
@app.delete("/expenses/{expense_id}")
def delete_expense(expense_id: int):

    for expense in expenses:
        if expense["id"] == expense_id:
            expenses.remove(expense)
            return {"message": "Expense deleted successfully"}

    raise HTTPException(status_code=404, detail="Expense not found")
