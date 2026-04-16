import pytest
from fastapi.testclient import TestClient
from main import app
from backend.app.api.database import Base, engine

client = TestClient(app)

# Reset DB before tests
@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

# ── REGISTRATION TESTS ──
def test_register_success():
    res = client.post("/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "test123"
    })
    assert res.status_code == 200
    assert res.json()["username"] == "testuser"

def test_register_duplicate_user():
    client.post("/register", json={"username": "testuser", "email": "test@example.com", "password": "test123"})
    res = client.post("/register", json={"username": "testuser", "email": "test@example.com", "password": "test123"})
    assert res.status_code == 400  # duplicate

# ── LOGIN TESTS ─────────────────────────────────────────────────
def test_login_success():
    client.post("/register", json={"username": "testuser", "email": "test@example.com", "password": "test123"})
    res = client.post("/login", data={"username": "testuser", "password": "test123"})
    assert res.status_code == 200
    assert "access_token" in res.json()

def test_login_wrong_password():
    client.post("/register", json={"username": "testuser", "email": "test@example.com", "password": "test123"})
    res = client.post("/login", data={"username": "testuser", "password": "wrongpass"})
    assert res.status_code == 401

def test_login_nonexistent_user():
    res = client.post("/login", data={"username": "nobody", "password": "pass"})
    assert res.status_code == 401

# ── HELPER ──────────────────────────────────────────────────────
def get_token():
    client.post("/register", json={"username": "testuser", "email": "test@example.com", "password": "test123"})
    res = client.post("/login", data={"username": "testuser", "password": "test123"})
    return res.json()["access_token"]

# ── EXPENSE TESTS ───────────────────────────────────────────────
def test_add_expense():
    token = get_token()
    res = client.post("/expenses",
        json={"title": "Biryani", "amount": 150.0, "category": "Food", "date": "2026-03-12"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    assert res.json()["title"] == "Biryani"
    assert res.json()["amount"] == 150.0

def test_add_expense_missing_fields():
    token = get_token()
    res = client.post("/expenses",
        json={"title": "Biryani"},  # missing amount and category
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 422  # validation error

def test_get_expenses():
    token = get_token()
    res = client.get("/expenses", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert isinstance(res.json(), list)

def test_get_expenses_unauthorized():
    res = client.get("/expenses")
    assert res.status_code == 401

def test_update_expense():
    token = get_token()
    add = client.post("/expenses",
        json={"title": "Cab", "amount": 200.0, "category": "Transport", "date": "2026-03-12"},
        headers={"Authorization": f"Bearer {token}"}
    )
    exp_id = add.json()["id"]
    res = client.put(f"/expenses/{exp_id}",
        json={"title": "Uber", "amount": 250.0, "category": "Transport", "date": "2026-03-12"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    assert res.json()["title"] == "Uber"
    assert res.json()["amount"] == 250.0

def test_update_nonexistent_expense():
    token = get_token()
    res = client.put("/expenses/9999",
        json={"title": "X", "amount": 100.0, "category": "Food", "date": "2026-03-12"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 404

def test_delete_expense():
    token = get_token()
    add = client.post("/expenses",
        json={"title": "Coffee", "amount": 50.0, "category": "Food", "date": "2026-03-12"},
        headers={"Authorization": f"Bearer {token}"}
    )
    exp_id = add.json()["id"]
    res = client.delete(f"/expenses/{exp_id}", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200

def test_delete_nonexistent_expense():
    token = get_token()
    res = client.delete("/expenses/9999", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 404

def test_user_cannot_access_others_expenses():
    # User 1
    client.post("/register", json={"username": "user1", "email": "u1@test.com", "password": "pass123"})
    token1 = client.post("/login", data={"username": "user1", "password": "pass123"}).json()["access_token"]
    add = client.post("/expenses",
        json={"title": "Private", "amount": 100.0, "category": "Food", "date": "2026-03-12"},
        headers={"Authorization": f"Bearer {token1}"}
    )
    exp_id = add.json()["id"]

    # User 2 tries to delete user 1's expense
    client.post("/register", json={"username": "user2", "email": "u2@test.com", "password": "pass123"})
    token2 = client.post("/login", data={"username": "user2", "password": "pass123"}).json()["access_token"]
    res = client.delete(f"/expenses/{exp_id}", headers={"Authorization": f"Bearer {token2}"})
    assert res.status_code == 404  # should not be accessible