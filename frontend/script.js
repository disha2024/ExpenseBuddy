const API_URL = "http://127.0.0.1:8000";

async function fetchExpenses() {
    const response = await fetch(`${API_URL}/expenses`);
    const data = await response.json();

    const table = document.getElementById("expenseTable");
    const emptyState = document.getElementById("emptyState");
    const totalAmount = document.getElementById("totalAmount");

    table.innerHTML = "";
    let total = 0;

    if (data.length === 0) {
        emptyState.style.display = "block";
    } else {
        emptyState.style.display = "none";
    }

    data.forEach(expense => {
        total += expense.amount;

        const row = `
            <tr>
                <td>${expense.id}</td>
                <td>${expense.title}</td>
                <td>₹${expense.amount}</td>
                <td>${expense.category}</td>
                <td>${expense.date}</td>
                <td>
                    <button class="edit-btn" onclick="editExpense(${expense.id}, '${expense.title}', ${expense.amount}, '${expense.category}', '${expense.date}')">Edit</button>
                    <button class="delete-btn" onclick="deleteExpense(${expense.id})">Delete</button>
                </td>
            </tr>
        `;
        table.innerHTML += row;
    });

    totalAmount.innerText = total.toFixed(2);
}

async function addOrUpdateExpense() {
    const id = document.getElementById("expense_id").value;
    const title = document.getElementById("title").value;
    const amount = document.getElementById("amount").value;
    const category = document.getElementById("category").value;
    const date = document.getElementById("date").value;

    if (!title || !amount || !category || !date) {
        showMessage("⚠️ Please fill all fields", "red");
        return;
    }

    const expenseData = {
        title: title,
        amount: Number(amount),
        category: category,
        date: date
    };

    let response;

    if (id) {
        response = await fetch(`${API_URL}/expenses/${id}`, {
            method: "PUT",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(expenseData)
        });
    } else {
        response = await fetch(`${API_URL}/expenses`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(expenseData)
        });
    }

    if (response.ok) {
        showMessage("✅ Expense Saved Successfully!", "green");
        clearFields();
        fetchExpenses();
    } else {
        showMessage("❌ Something went wrong!", "red");
    }
}

function editExpense(id, title, amount, category, date) {
    document.getElementById("expense_id").value = id;
    document.getElementById("title").value = title;
    document.getElementById("amount").value = amount;
    document.getElementById("category").value = category;
    document.getElementById("date").value = date;
}

async function deleteExpense(id) {
    if (!confirm("⚠️ Are you sure you want to delete this expense?")) return;

    await fetch(`${API_URL}/expenses/${id}`, {
        method: "DELETE"
    });

    showMessage("🗑️ Expense Deleted Successfully!", "green");
    fetchExpenses();
}

function clearFields() {
    document.getElementById("expense_id").value = "";
    document.getElementById("title").value = "";
    document.getElementById("amount").value = "";
    document.getElementById("category").value = "";
    document.getElementById("date").value = "";
}

function showMessage(message, color) {
    const msg = document.getElementById("message");
    msg.innerText = message;
    msg.style.color = color;

    setTimeout(() => {
        msg.innerText = "";
    }, 3000);
}

fetchExpenses();
