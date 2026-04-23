// Prevent duplicate declaration errors
if (typeof API_BASE === 'undefined') {
    window.API_BASE = window.location.origin;
}

function getToken() { return localStorage.getItem("access_token"); }
function getCurrencySymbol() { return localStorage.getItem("currency_symbol") || "₹"; }

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


async function addExpense(event) {
    if (event) event.preventDefault();

    const select = document.getElementById("categorySelect");
    const customInput = document.getElementById("customCategoryInput");
    
    // Logic: Use the dropdown value, UNLESS it's 'others', then use the custom text
    let finalCategory = select.value;
    if (select.value === "others") {
        finalCategory = customInput.value.trim();
    }

    if (!finalCategory) {
        alert("Please select or type a category!");
        return;
    }

    const expenseData = {
        title: document.getElementById("title").value,
        amount: parseFloat(document.getElementById("amount").value),
        category_name: finalCategory, // This is what your backend expects
        date: document.getElementById("date").value || null
    };


    const res = await fetch(`${API_BASE}/expenses`, {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${getToken()}`
        },
        body: JSON.stringify(expenseData)
    });

    if (res.ok) {
        alert("Saved!");
        location.reload();
    }
}



async function updateExpense(id, title, amountDecimal, category, date) {
    const subunits = Math.round(parseFloat(amountDecimal) * 100);
    const response = await fetch(`${API_BASE}/expenses/${id}`, {
        method: "PUT",
        headers: { 
            "Content-Type": "application/json", 
            "Authorization": `Bearer ${getToken()}` 
        },
        body: JSON.stringify({ 
            title, 
            amount: subunits, 
            category_name: category, 
            date: date || null 
        })
    });
    if (response.ok) { clearForm(); loadExpenses(); }
}

// 1. Show/Hide custom category input
function toggleCustomCategory() {
    const select = document.getElementById("categorySelect");
    const customInput = document.getElementById("customCategoryInput");
    
    if (select.value === "others") {
        customInput.style.display = "block";
        customInput.focus();
    } else {
        customInput.style.display = "none";
        customInput.value = "";
    }
}

// 2. Main function to gather data and POST
async function saveExpense(event) {
    if (event) event.preventDefault();

    const title = document.getElementById("title").value;
    const amount = document.getElementById("amount").value;
    const date = document.getElementById("date").value;
    
    // Pick between dropdown or custom input
    const select = document.getElementById("categorySelect");
    const customInput = document.getElementById("customCategoryInput");
    const categoryName = (select.value === "others") ? customInput.value : select.value;

    if (!title || !amount || !categoryName || !date) {
        alert("⚠️ Please fill in all fields!");
        return;
    }

    const expenseData = {
        title: title,
        amount: parseFloat(amount), 
        category_name: categoryName, // String for your get_or_create logic
        date: date
    };

    try {
        const response = await fetch(`${API_BASE}/expenses`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${getToken()}`
            },
            body: JSON.stringify(expenseData)
        });

        if (response.ok) {
            alert("✅ Expense Saved!");
            location.reload(); 
        } else {
            const err = await response.json();
            alert("❌ Error: " + (err.detail || "Upload failed"));
        }
    } catch (error) {
        console.error("Fetch error:", error);
        alert("❌ Server is unreachable.");
    }
}


async function saveExpense(event) {
    if (event) event.preventDefault();

    // 1. Get the elements safely
    const titleEl = document.getElementById("title");
    const amountEl = document.getElementById("amount");
    const dateEl = document.getElementById("date");
    const selectEl = document.getElementById("categorySelect");
    const customInputEl = document.getElementById("customCategoryInput");

    // 2. Check if elements exist to prevent "null" errors
    if (!titleEl || !amountEl || !dateEl || !selectEl) {
        console.error("Missing elements: check if IDs in HTML match script.js");
        return;
    }

    // 3. Logic: Use the dropdown value, UNLESS it's 'others'
    let finalCategory = selectEl.value;
    if (selectEl.value === "others" && customInputEl) {
        finalCategory = customInputEl.value.trim();
    }

    // 4. Validate that no fields are empty
    if (!titleEl.value || !amountEl.value || !finalCategory || !dateEl.value) {
        alert("⚠️ Please fill in all fields (Title, Amount, Category, and Date)");
        return;
    }

    // 5. Prepare the Data Object
    const expenseData = {
        title: titleEl.value,
        amount: parseFloat(amountEl.value),
        category_name: finalCategory,
        date: dateEl.value
    };

    // 6. Send the POST Request
    const token = localStorage.getItem("access_token");
    if (!token) {
        alert("You are not logged in!");
        return;
    }

    try {
        console.log("Sending POST request to /expenses...", expenseData);
        
        const res = await fetch(`${API_BASE}/expenses`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "Authorization": `Bearer ${token}`
            },
            body: JSON.stringify(expenseData)
        });

        if (res.ok) {
            const savedExpense = await res.json();
            console.log("Success:", savedExpense);
            alert("✅ Expense saved successfully!");
            
            // Reload page to show new item in History
            location.reload(); 
        } else {
            const errorData = await res.json();
            console.error("Server Error:", errorData);
            alert("❌ Failed to save: " + (errorData.detail || "Unknown error"));
        }
    } catch (error) {
        console.error("Network Error:", error);
        alert("❌ Error: Could not connect to the server.");
    }
}
function clearForm() {
    document.getElementById("expense_id").value = "";
    document.getElementById("title").value = "";
    document.getElementById("amount").value = "";
    document.getElementById("category").value = "";
    document.getElementById("date").value = "";
    document.getElementById("saveBtn").innerHTML = "💾 Save Expense";
    document.getElementById("cancelBtn").style.display = "none";
}

function editExpense(id, title, decimalAmount, category, date) {
    document.getElementById("expense_id").value = id;
    document.getElementById("title").value = title;
    document.getElementById("amount").value = decimalAmount; 
    document.getElementById("category").value = category;
    document.getElementById("date").value = date;
    
    document.getElementById("saveBtn").innerHTML = "🔄 Update Expense";
    document.getElementById("cancelBtn").style.display = "inline-block";
    window.scrollTo({ top: 0, behavior: 'smooth' });
}


function displayExpenses(expenses) {
    const tableBody = document.getElementById("expenseTable");
    const totalBox = document.getElementById("totalAmount");
    const emptyState = document.getElementById("emptyState");

    // Safety check to ensure elements exist
    if (!tableBody || !totalBox) return;

    // Clear the current table rows
    tableBody.innerHTML = "";
    
    let totalSubunits = 0;

    // Loop through each expense
    expenses.forEach(exp => {
        // 1. Accumulate the total using the raw integer (subunit)
        const amt = Number(exp.amount) || 0;
        totalSubunits += amt;

        // 2. Format for display (Lowest Denomination: 3000 -> 30.00)
        const decimalDisplay = (amt / 100).toFixed(2);
        
        const categoryName = exp.category_name || "General";
        const expenseDate = exp.date || "N/A";

        // 3. Create and append the row
        const row = document.createElement("tr");
        row.innerHTML = `
            <td>${exp.title}</td>
            <td>${getCurrencySymbol()}${decimalDisplay}</td>
            <td>${categoryName}</td>
            <td>${expenseDate}</td>
            <td style="display: flex; gap: 8px; justify-content: center;">
                <button class="edit-btn" onclick="editExpense(${exp.id}, '${exp.title.replace(/'/g, "\\'")}', ${decimalDisplay}, '${categoryName}', '${expenseDate}')">✏️</button>
                <button class="delete-btn" onclick="deleteExpense(${exp.id})">🗑️</button>
            </td>
        `;
        tableBody.appendChild(row);
    });

    // 4. Update the Total Spent box (Total Subunits / 100)
    totalBox.textContent = (totalSubunits / 100).toFixed(2);

    // 5. Toggle the "No expenses recorded yet" message
    if (emptyState) {
        if (expenses.length > 0) {
            emptyState.style.display = "none";  // Hide if there is data
        } else {
            emptyState.style.display = "block"; // Show if table is empty
        }
    }
}


async function loadExpenses() {
    const res = await fetch(`${API_BASE}/expenses`, { 
        headers: { "Authorization": `Bearer ${getToken()}` } 
    });
    if (res.ok) displayExpenses(await res.json());
}

async function deleteExpense(id) {
    if (!confirm("Are you sure you want to delete this expense?")) return;

    const response = await fetch(`${API_BASE}/expenses/${id}`, {
        method: "DELETE",
        headers: { "Authorization": `Bearer ${getToken()}` }
    });

    if (response.ok) {
        loadExpenses(); 
    } else {
        alert("Delete failed on server.");
    }
}



// Attach to window so onclick works even if loaded as a module
window.saveExpense = saveExpense;
window.deleteExpense = deleteExpense;
window.editExpense = editExpense;
window.clearForm = clearForm;