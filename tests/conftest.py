import os

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import get_db
from app.main import app
from app.models import Base, User
from app.security import hash_password


load_dotenv()

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")

if not TEST_DATABASE_URL:
    raise RuntimeError("TEST_DATABASE_URL is not set")


test_engine = create_engine(TEST_DATABASE_URL)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=test_engine,
)


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)

    with test_engine.begin() as connection:
        connection.exec_driver_sql(
            "ALTER SEQUENCE users_id_seq RESTART WITH 1"
        )

    def override_get_db():
        db = TestingSessionLocal()

        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    yield

    app.dependency_overrides.clear()

@pytest.fixture
def test_password():
    return "testpassword123"

@pytest.fixture
def test_user(test_password):
    db = TestingSessionLocal()

    user = User(
        username="testuser",
        hashed_password=hash_password(test_password),
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()

    return user

@pytest.fixture
def test_user(test_password):
    db = TestingSessionLocal()

    user = User(
        username="testuser",
        hashed_password=hash_password(test_password),
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()

    return user

@pytest.fixture
def alice_password():
    return "alicepassword123"

@pytest.fixture
def alice_user(alice_password):
    db = TestingSessionLocal()

    user = User(
        username="alice",
        hashed_password=hash_password(alice_password),
    )

    db.add(user)
    db.commit()
    db.refresh(user)
    db.close()

    return user

@pytest.fixture
def client():
    with TestClient(app) as client:
        yield client


@pytest.fixture
def login(client, test_user, test_password):
    def _login(
        username=None,
        password=None,
    ):
        if username is None:
            username = test_user.username

        if password is None:
            password = test_password

        response = client.post(
            "/token",
            data={
                "username": username,
                "password": password,
            },
        )

        assert response.status_code == 200

        token = response.json()["access_token"]

        return {
            "Authorization": f"Bearer {token}"
        }

    return _login


@pytest.fixture
def authenticated_client(client, login):
    headers = login()

    client.headers.update(headers)

    return client