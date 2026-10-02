from fastapi.testclient import TestClient

from tests.conftest import TestingSessionLocal
from app.models import User


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
    test_user
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
    test_user
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
    authenticated_client: TestClient,
):
    response = authenticated_client.get("/users/me")

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

def test_users_me_rejects_malformed_authorization_header(
    client: TestClient,
):
    response = client.get(
        "/users/me",
        headers={
            "Authorization": "NotBearer token"
        },
    )

    assert response.status_code == 401

def test_register_requires_username(
    client: TestClient,
):
    response = client.post(
        "/users",
        json={
            "password": "somepassword123",
        },
    )

    assert response.status_code == 422

def test_register_requires_password(
    client: TestClient,
):
    response = client.post(
        "/users",
        json={
            "username": "alice",
        },
    )

    assert response.status_code == 422

def test_login_requires_username(
    client: TestClient,
):
    response = client.post(
        "/token",
        data={
            "password": "testpassword123",
        },
    )

    assert response.status_code == 422

def test_login_requires_password(
    client: TestClient,
):
    response = client.post(
        "/token",
        data={
            "username": "testuser",
        },
    )

    assert response.status_code == 422

def test_register_hashes_password(
    client: TestClient,
):
    password = "somepassword123"

    response = client.post(
        "/users",
        json={
            "username": "bob",
            "password": password,
        },
    )

    assert response.status_code == 201

    db = TestingSessionLocal()

    user = db.query(User).filter(
        User.username == "bob"
    ).first()

    db.close()

    assert user is not None
    assert user.hashed_password != password
    assert user.hashed_password.startswith("$argon2")

def test_register_username_cannot_be_empty(client: TestClient):
    response = client.post(
        "/users",
        json={
            "username": "",
            "password": "testpassword123",
        },
    )

    assert response.status_code == 422


def test_register_password_cannot_be_empty(client: TestClient):
    response = client.post(
        "/users",
        json={
            "username": "newuser",
            "password": "",
        },
    )

    assert response.status_code == 422


def test_login_with_empty_password(client: TestClient, test_user):
    response = client.post(
        "/token",
        data={
            "username": "testuser",
            "password": "",
        },
    )

    assert response.status_code == 422


def test_login_with_empty_username(client: TestClient, test_user):
    response = client.post(
        "/token",
        data={
            "username": "",
            "password": "testpassword123",
        },
    )

    assert response.status_code == 422


def test_users_me_rejects_expired_or_invalid_token(client: TestClient):
    response = client.get(
        "/users/me",
        headers={
            "Authorization": "Bearer invalid.token.here"
        },
    )

    assert response.status_code == 401

def test_register_username_too_short(client: TestClient):
    response = client.post(
        "/users",
        json={
            "username": "ab",
            "password": "testpassword123",
        },
    )

    assert response.status_code == 422


def test_register_password_too_short(client: TestClient):
    response = client.post(
        "/users",
        json={
            "username": "newuser",
            "password": "1234567",
        },
    )

    assert response.status_code == 422


def test_register_username_too_long(client: TestClient):
    response = client.post(
        "/users",
        json={
            "username": "a" * 51,
            "password": "testpassword123",
        },
    )

    assert response.status_code == 422


def test_register_password_too_long(client: TestClient):
    response = client.post(
        "/users",
        json={
            "username": "newuser",
            "password": "a" * 129,
        },
    )

    assert response.status_code == 422

def test_register_username_min_length_allowed(client: TestClient):
    response = client.post(
        "/users",
        json={
            "username": "abc",
            "password": "testpassword123",
        },
    )

    assert response.status_code == 201


def test_register_password_min_length_allowed(client: TestClient):
    response = client.post(
        "/users",
        json={
            "username": "newuser",
            "password": "12345678",
        },
    )

    assert response.status_code == 201


def test_register_username_max_length_allowed(client: TestClient):
    response = client.post(
        "/users",
        json={
            "username": "a" * 50,
            "password": "testpassword123",
        },
    )

    assert response.status_code == 201


def test_register_password_max_length_allowed(client: TestClient):
    response = client.post(
        "/users",
        json={
            "username": "newuser",
            "password": "a" * 128,
        },
    )

    assert response.status_code == 201