from fastapi.testclient import TestClient


def test_users_me_requires_authentication(
    client: TestClient,
):
    response = client.get("/users/me")

    assert response.status_code == 401

    assert response.json() == {
        "detail": "Not authenticated"
    }


def test_login_with_invalid_username(
    client: TestClient,
):
    response = client.post(
        "/token",
        data={
            "username": "definitely_not_a_real_user",
            "password": "wrongpassword",
        },
    )

    assert response.status_code == 401

    assert response.json() == {
        "detail": "Incorrect username or password"
    }


def test_login_with_invalid_password(
    client: TestClient,
):
    response = client.post(
        "/token",
        data={
            "username": "testuser",
            "password": "wrongpassword",
        },
    )

    assert response.status_code == 401

    assert response.json() == {
        "detail": "Incorrect username or password"
    }


def test_register_existing_username(
    client: TestClient,
):
    response = client.post(
        "/users",
        json={
            "username": "testuser",
            "password": "somepassword123",
        },
    )

    assert response.status_code == 409

    assert response.json() == {
        "detail": "Username already exists"
    }


def test_register_new_user(
    client: TestClient,
):
    response = client.post(
        "/users",
        json={
            "username": "alice",
            "password": "alicepassword123",
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["username"] == "alice"
    assert "id" in body
    assert "hashed_password" not in body
    assert "password" not in body


def test_login_success(
    client: TestClient,
):
    response = client.post(
        "/token",
        data={
            "username": "testuser",
            "password": "testpassword123",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert "access_token" in body
    assert isinstance(body["access_token"], str)
    assert body["token_type"] == "bearer"


def test_users_me_returns_current_user(
    client: TestClient,
    login,
):
    headers = login()

    response = client.get(
        "/users/me",
        headers=headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert body["username"] == "testuser"
    assert body["id"] == 1


def test_users_me_rejects_invalid_token(
    client: TestClient,
):
    response = client.get(
        "/users/me",
        headers={
            "Authorization": "Bearer definitely-not-a-valid-token"
        },
    )

    assert response.status_code == 401