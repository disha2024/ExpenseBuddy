// 1. Initialize Globals
if (typeof API_BASE === 'undefined') {
    window.API_BASE = window.location.origin;
}

function getToken() { return localStorage.getItem("access_token"); }
function getCurrencySymbol() { return localStorage.getItem("currency_symbol") || "₹"; }

// 2. UI Helper for Custom Category
function toggleCustomCategory() {
    const select = document.getElementById("categorySelect");
    const customInput = document.getElementById("customCategoryInput");
    
    if (select && select.value === "others") {
        customInput.style.display = "block";
        customInput.focus();
    } else if (customInput) {
        customInput.style.display = "none";
        customInput.value = "";
    }
}

async function saveExpense(event) {
    if (event) event.preventDefault();

    const titleEl = document.getElementById("title");
    const amountEl = document.getElementById("amount");
    const dateEl = document.getElementById("date");
    const selectEl = document.getElementById("categorySelect");
    const customInputEl = document.getElementById("customCategoryInput");

    // Fix the ReferenceError: Define the category name logic
    let finalCategory = selectEl.value;
    if (selectEl.value === "others" && customInputEl) {
        finalCategory = customInputEl.value.trim();
    }

    if (!titleEl.value || !amountEl.value || !finalCategory || !dateEl.value) {
        alert("⚠️ Please fill in all fields");
        return;
    }

    const expenseData = {
        title: titleEl.value,
        // Fix the unit mismatch: Multiply by 100
        amount: Math.round(parseFloat(amountEl.value) * 100), 
        category_name: finalCategory,
        date: dateEl.value
    };

    try {
        const res = await fetch(`${API_BASE}/expenses/`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${localStorage.getItem("access_token")}`
            },
            body: JSON.stringify(expenseData)
        });

        if (res.ok) {
            alert("✅ Expense saved successfully!");
            location.reload(); 
        } else {
            const err = await res.json();
            alert("❌ Save failed: " + (err.detail || "Check console"));
        }
    } catch (error) {
        console.error("Save error:", error);
    }
}

  

// 4. Loading and Displaying Data
async function loadCategories() {
    try {
        const response = await fetch(`${API_BASE}/categories`, {
            headers: { "Authorization": `Bearer ${getToken()}` }
        });
        if (response.ok) {
            const categories = await response.json();
            const datalist = document.getElementById("categoryList");
            if (!datalist) return; 
            datalist.innerHTML = "";
            categories.forEach(cat => {
                const option = document.createElement("option");
                option.value = cat.name;
                datalist.appendChild(option);
            });
        }
    } catch (err) { console.error(err); }
}

async function loadExpenses() {
    const res = await fetch(`${API_BASE}/expenses`, { 
        headers: { "Authorization": `Bearer ${getToken()}` } 
    });
    if (res.ok) displayExpenses(await res.json());
}

function displayExpenses(expenses) {
    const tableBody = document.getElementById("expenseTable");
    const totalBox = document.getElementById("totalAmount");
    const emptyState = document.getElementById("emptyState");

    if (!tableBody || !totalBox) return;

    tableBody.innerHTML = "";
    let totalSubunits = 0;

    expenses.forEach(exp => {
        const amt = Number(exp.amount) || 0;
        totalSubunits += amt;
        const decimalDisplay = (amt / 100).toFixed(2);
        
        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${exp.title}</td>
            <td>${getCurrencySymbol()}${decimalDisplay}</td>
            <td>${exp.category_name || "General"}</td>
            <td>${exp.date || "N/A"}</td>
            <td style="display: flex; gap: 8px; justify-content: center;">
                <button class="edit-btn" onclick="editExpense(${exp.id}, '${exp.title.replace(/'/g, "\\'")}', ${decimalDisplay}, '${exp.category_name}', '${exp.date}')">✏️</button>
                <button class="delete-btn" onclick="deleteExpense(${exp.id})">🗑️</button>
            </td>
        `;
        tableBody.appendChild(row);
    });

    totalBox.textContent = (totalSubunits / 100).toFixed(2);
    if (emptyState) emptyState.style.display = expenses.length > 0 ? "none" : "block";
}

function editExpense(id, title, decimalDisplay, category, date) {
    // Fill the inputs
    document.getElementById("expense_id").value = id;
    document.getElementById("title").value = title;
    
    // Ensure this is the decimal version (e.g., 5.50)
    document.getElementById("amount").value = decimalDisplay; 
    document.getElementById("date").value = date;
    
    const select = document.getElementById("categorySelect");
    if (select) select.value = category;

    // Change Save button to Update
    const saveBtn = document.getElementById("saveBtn");
    const cancelBtn = document.getElementById("cancelBtn");
    
    if (saveBtn) {
        saveBtn.innerHTML = "🔄 Update Expense";
        // Pass the ID to the update logic
        saveBtn.onclick = (e) => updateExpenseLogic(e, id);
    }
    if (cancelBtn) cancelBtn.style.display = "inline-block";
}

async function updateExpenseLogic(event, id) {
    if (event) event.preventDefault();

    const titleEl = document.getElementById("title");
    const amountEl = document.getElementById("amount");
    const dateEl = document.getElementById("date");
    const selectEl = document.getElementById("categorySelect");
    const customInputEl = document.getElementById("customCategoryInput");

    // 1. FIX THE REFERENCE ERROR: Define how to get the category name
    let categoryName = selectEl.value;
    if (selectEl.value === "others" && customInputEl) {
        categoryName = customInputEl.value.trim();
    }

    // 2. Validation
    if (!titleEl.value || !amountEl.value || !categoryName || !dateEl.value) {
        alert("⚠️ Please fill in all fields");
        return;
    }

    const expenseData = {
        title: titleEl.value,
        amount: Math.round(parseFloat(amountEl.value) * 100),
        category_name: categoryName,
        date: dateEl.value
    };

    try {
        const res = await fetch(`${API_BASE}/expenses/${id}`, {
            method: "PUT",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${localStorage.getItem("access_token")}`
            },
            body: JSON.stringify(expenseData)
        });

        if (res.ok) {
            alert("✅ Updated successfully!");
            clearForm(); // This will reset the button back to "Save"
            location.reload(); 
        } else {
            const err = await res.json();
            alert("❌ Update failed: " + (err.detail || "Check console"));
        }
    } catch (error) {
        console.error("Update error:", error);
    }
}


async function deleteExpense(id) {
    if (!confirm("Are you sure?")) return;
    const res = await fetch(`${API_BASE}/expenses/${id}`, {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${getToken()}` }
    });
    if (res.ok) loadExpenses();
}

function clearForm() {
    // 1. Clear all inputs
    document.getElementById("expense_id").value = "";
    document.getElementById("title").value = "";
    document.getElementById("amount").value = "";
    document.getElementById("date").value = "";
    document.getElementById("categorySelect").value = "";
    
    // 2. Reset the Save Button
    const saveBtn = document.getElementById("saveBtn");
    if (saveBtn) {
        saveBtn.innerHTML = "💾 Save Expense";
        saveBtn.onclick = (e) => saveExpense(e); // Set it back to save
    }

    // 3. Hide the Cancel button
    const cancelBtn = document.getElementById("cancelBtn");
    if (cancelBtn) cancelBtn.style.display = "none";
}

// 5. Expose functions to the HTML window
window.toggleCustomCategory = toggleCustomCategory;
window.saveExpense = saveExpense;
window.deleteExpense = deleteExpense;
window.clearForm = clearForm;
window.editExpense = editExpense;
window.updateExpenseLogic = updateExpenseLogic;