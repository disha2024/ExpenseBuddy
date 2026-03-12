const API_BASE = "http://127.0.0.1:8000";

// GET TOKEN FROM LOCAL STORAGE
function getToken() {
    return localStorage.getItem("access_token");
}

// ADD EXPENSE
async function addExpense(title, amount, category, date) {
    try {
        const token = getToken();
        if (!token) {
            alert("You must be logged in to add an expense");
            return;
        }

        const response = await fetch(`${API_BASE}/expenses`, {
            method: "POST",
            headers: { 
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },
            body: JSON.stringify({ title, amount, category, date: date || null })
        });

        if (response.ok) {
            alert("Expense Added Successfully!");
            clearForm();
            loadExpenses();
        } else {
            const error = await response.json();
            console.log("Error:", error);
            alert("Error adding expense: " + JSON.stringify(error.detail));
        }
    } catch (err) {
        console.error("Error:", err);
        alert("Server not reachable");
    }
}

// UPDATE EXPENSE
async function updateExpense(id, title, amount, category, date) {
    try {
        const token = getToken();
        if (!token) {
            alert("You must be logged in to update an expense");
            return;
        }

        const response = await fetch(`${API_BASE}/expenses/${id}`, {
            method: "PUT",
            headers: { 
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },
            body: JSON.stringify({ title, amount, category, date: date || null })
        });

        if (response.ok) {
            alert("Expense Updated Successfully!");
            clearForm();
            loadExpenses();
        } else {
            const error = await response.json();
            console.log("Error:", error);
            alert("Error updating expense: " + JSON.stringify(error.detail));
        }
    } catch (err) {
        console.error("Error:", err);
        alert("Server not reachable");
    }
}

// SAVE EXPENSE (Create or Update)
function saveExpense() {
    const expense_id = document.getElementById("expense_id").value;
    const title = document.getElementById("title").value.trim();
    const amount = parseFloat(document.getElementById("amount").value);
    const category = document.getElementById("category").value.trim();
    const date = document.getElementById("date").value;

    if (!title || !amount || !category) {
        alert("Please fill in all fields");
        return;
    }

    if (expense_id) {
        updateExpense(parseInt(expense_id), title, amount, category, date);
    } else {
        addExpense(title, amount, category, date);
    }
}

// CLEAR FORM
function clearForm() {
    document.getElementById("title").value = "";
    document.getElementById("amount").value = "";
    document.getElementById("category").value = "";
    document.getElementById("date").value = "";
    document.getElementById("expense_id").value = "";
    document.getElementById("message").textContent = "";
    document.getElementById("cancelBtn").style.display = "none";
}

// EDIT EXPENSE
function editExpense(id, title, amount, category, date) {
    document.getElementById("expense_id").value = id;
    document.getElementById("title").value = title;
    document.getElementById("amount").value = amount;
    document.getElementById("category").value = category;
    document.getElementById("date").value = date;
    document.getElementById("cancelBtn").style.display = "inline-block";
    
    // Scroll to top
    window.scrollTo(0, 0);
}

// CANCEL EDIT
function cancelEdit() {
    clearForm();
}

// FILTER EXPENSES
async function filterExpenses() {
    const filterCategory = document.getElementById("filterCategory").value.trim().toLowerCase();
    
    if (!filterCategory) {
        loadExpenses();
        return;
    }

    try {
        const token = getToken();
        if (!token) {
            alert("You must be logged in");
            return;
        }

        const response = await fetch(`${API_BASE}/expenses`, {
            headers: {
                "Authorization": `Bearer ${token}`
            }
        });

        if (!response.ok) {
            alert("Error fetching expenses");
            return;
        }

        const expenses = await response.json();
        const filtered = expenses.filter(exp => 
            exp.category.toLowerCase().includes(filterCategory)
        );

        displayExpenses(filtered);
    } catch (err) {
        console.error("Error:", err);
    }
}

// DISPLAY EXPENSES
function displayExpenses(expenses) {
    const tableBody = document.getElementById("expenseTable");
    const emptyState = document.getElementById("emptyState");

    tableBody.innerHTML = "";

    if (expenses.length === 0) {
        emptyState.style.display = "block";
        return;
    }

    emptyState.style.display = "none";

    let totalAmount = 0;

    expenses.forEach(expense => {
        totalAmount += expense.amount;

        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${expense.id}</td>
            <td>${expense.title}</td>
            <td>₹${expense.amount.toFixed(2)}</td>
            <td>${expense.category}</td>
            <td>${expense.date}</td>
            <td>
                <button class="edit-btn" onclick="editExpense(${expense.id}, '${expense.title}', ${expense.amount}, '${expense.category}', '${expense.date}')">✏️ Edit</button>
                <button class="delete-btn" onclick="deleteExpense(${expense.id})">🗑️ Delete</button>
            </td>
        `;
        tableBody.appendChild(row);
    });

    document.getElementById("totalAmount").textContent = totalAmount.toFixed(2);
}

// LOAD EXPENSES (Complete version)
async function loadExpenses() {
    try {
        const token = getToken();
        if (!token) {
            alert("You must be logged in");
            return;
        }

        const response = await fetch(`${API_BASE}/expenses`, {
            headers: {
                "Authorization": `Bearer ${token}`
            }
        });

        if (!response.ok) {
            alert("Error fetching expenses");
            return;
        }

        const expenses = await response.json();
        displayExpenses(expenses);
    } catch (err) {
        console.error("Error:", err);
    }
}

// DELETE EXPENSE
async function deleteExpense(id) {
    if (!confirm("Are you sure you want to delete this expense?")) return;

    try {
        const token = getToken();
        if (!token) {
            alert("You must be logged in to delete an expense");
            return;
        }

        const response = await fetch(`${API_BASE}/expenses/${id}`, {
            method: "DELETE",
            headers: {
                "Authorization": `Bearer ${token}`
            }
        });

        if (response.ok) {
            loadExpenses();
        } else {
            alert("Error deleting expense");
        }
    } catch (err) {
        console.error("Error:", err);
    }
}
