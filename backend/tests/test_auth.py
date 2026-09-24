def test_register_artist(client):
    response = client.post(
        "/auth/register",
        json={
            "full_name": "Test Artist",
            "email": "testartist@example.com",
            "password": "securepassword123",
            "state": "Karnataka"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["email"] == "testartist@example.com"
    assert data["full_name"] == "Test Artist"

def test_register_duplicate_email(client):
    payload = {
        "full_name": "Artist One",
        "email": "duplicate@example.com",
        "password": "password123"
    }
    res1 = client.post("/auth/register", json=payload)
    assert res1.status_code == 200

    res2 = client.post("/auth/register", json=payload)
    assert res2.status_code == 400
    assert "already exists" in res2.json()["detail"]

def test_login_success(client):
    reg_payload = {
        "full_name": "Login User",
        "email": "loginuser@example.com",
        "password": "mypassword123"
    }
    client.post("/auth/register", json=reg_payload)

    login_res = client.post(
        "/auth/login",
        json={
            "email": "loginuser@example.com",
            "password": "mypassword123"
        }
    )
    assert login_res.status_code == 200
    data = login_res.json()
    assert "access_token" in data
    assert data["email"] == "loginuser@example.com"

def test_login_invalid_password(client):
    login_res = client.post(
        "/auth/login",
        json={
            "email": "loginuser@example.com",
            "password": "wrongpassword"
        }
    )
    assert login_res.status_code == 401
