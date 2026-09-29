from fastapi.testclient import TestClient


def test_create_url_requires_authentication(
    client: TestClient,
):
    response = client.post(
        "/urls",
        json={
            "url": "https://example.com/",
        },
    )

    assert response.status_code == 401


def test_create_url(
    client: TestClient,
    login,
):
    headers = login()

    response = client.post(
        "/urls",
        json={
            "url": "https://example.com/",
        },
        headers=headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert "id" in body
    assert "short_code" in body
    assert body["username"] == "testuser"

    assert len(body["short_code"]) == 7


def test_create_url_with_invalid_url(
    client: TestClient,
    login,
):
    headers = login()

    response = client.post(
        "/urls",
        json={
            "url": "not-a-valid-url",
        },
        headers=headers,
    )

    assert response.status_code == 422


def test_duplicate_url_returns_409(
    client: TestClient,
    login,
):
    headers = login()

    first_response = client.post(
        "/urls",
        json={
            "url": "https://example.com/",
        },
        headers=headers,
    )

    assert first_response.status_code == 200

    second_response = client.post(
        "/urls",
        json={
            "url": "https://example.com/",
        },
        headers=headers,
    )

    assert second_response.status_code == 409

    assert second_response.json() == {
        "detail": "URL already exists"
    }


def test_redirect_url(
    client: TestClient,
    login,
):
    headers = login()

    create_response = client.post(
        "/urls",
        json={
            "url": "https://github.com/",
        },
        headers=headers,
    )

    assert create_response.status_code == 200

    short_code = create_response.json()["short_code"]

    response = client.get(
        f"/{short_code}",
        follow_redirects=False,
    )

    assert response.status_code == 307
    assert response.headers["location"] == "https://github.com/"


def test_redirect_invalid_short_code(
    client: TestClient,
):
    response = client.get(
        "/doesnotexist",
        follow_redirects=False,
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "URL not found"
    }


def test_get_my_urls_requires_authentication(
    client: TestClient,
):
    response = client.get("/users/me/urls")

    assert response.status_code == 401


def test_get_my_urls(
    client: TestClient,
    login,
):
    headers = login()

    client.post(
        "/urls",
        json={
            "url": "https://example.com/",
        },
        headers=headers,
    )

    client.post(
        "/urls",
        json={
            "url": "https://github.com/",
        },
        headers=headers,
    )

    response = client.get(
        "/users/me/urls",
        headers=headers,
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body) == 2

    assert body[0]["original_url"] == "https://example.com/"
    assert body[1]["original_url"] == "https://github.com/"


def test_get_my_urls_pagination(
    client: TestClient,
    login,
):
    headers = login()

    urls = [
        "https://example.com/",
        "https://github.com/",
        "https://openai.com/",
        "https://fastapi.tiangolo.com/",
    ]

    for url in urls:
        response = client.post(
            "/urls",
            json={"url": url},
            headers=headers,
        )

        assert response.status_code == 200

    first_page = client.get(
        "/users/me/urls?skip=0&limit=2",
        headers=headers,
    )

    assert first_page.status_code == 200

    first_body = first_page.json()

    assert len(first_body) == 2
    assert first_body[0]["original_url"] == urls[0]
    assert first_body[1]["original_url"] == urls[1]

    second_page = client.get(
        "/users/me/urls?skip=2&limit=2",
        headers=headers,
    )

    assert second_page.status_code == 200

    second_body = second_page.json()

    assert len(second_body) == 2
    assert second_body[0]["original_url"] == urls[2]
    assert second_body[1]["original_url"] == urls[3]


def test_get_my_urls_limit_validation(
    client: TestClient,
    login,
):
    headers = login()

    response = client.get(
        "/users/me/urls?limit=101",
        headers=headers,
    )

    assert response.status_code == 422


def test_update_own_url(
    client: TestClient,
    login,
):
    headers = login()

    create_response = client.post(
        "/urls",
        json={
            "url": "https://example.com/",
        },
        headers=headers,
    )

    short_code = create_response.json()["short_code"]

    update_response = client.patch(
        f"/users/me/urls/{short_code}",
        json={
            "url": "https://github.com/",
        },
        headers=headers,
    )

    assert update_response.status_code == 200

    body = update_response.json()

    assert body["original_url"] == "https://github.com/"
    assert body["short_code"] == short_code


def test_update_invalid_url(
    client: TestClient,
    login,
):
    headers = login()

    create_response = client.post(
        "/urls",
        json={
            "url": "https://example.com/",
        },
        headers=headers,
    )

    short_code = create_response.json()["short_code"]

    response = client.patch(
        f"/users/me/urls/{short_code}",
        json={
            "url": "not-a-valid-url",
        },
        headers=headers,
    )

    assert response.status_code == 422


def test_update_missing_url_returns_404(
    client: TestClient,
    login,
):
    headers = login()

    response = client.patch(
        "/users/me/urls/doesnotexist",
        json={
            "url": "https://github.com/",
        },
        headers=headers,
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "URL not found"
    }


def test_delete_own_url(
    client: TestClient,
    login,
):
    headers = login()

    create_response = client.post(
        "/urls",
        json={
            "url": "https://example.com/",
        },
        headers=headers,
    )

    short_code = create_response.json()["short_code"]

    delete_response = client.delete(
        f"/users/me/urls/{short_code}",
        headers=headers,
    )

    assert delete_response.status_code == 204

    redirect_response = client.get(
        f"/{short_code}",
        follow_redirects=False,
    )

    assert redirect_response.status_code == 404


def test_delete_missing_url_returns_404(
    client: TestClient,
    login,
):
    headers = login()

    response = client.delete(
        "/users/me/urls/doesnotexist",
        headers=headers,
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "URL not found"
    }


def test_user_cannot_update_another_users_url(
    client: TestClient,
    login,
):
    owner_headers = login()

    create_response = client.post(
        "/urls",
        json={
            "url": "https://example.com/",
        },
        headers=owner_headers,
    )

    short_code = create_response.json()["short_code"]

    register_response = client.post(
        "/users",
        json={
            "username": "alice",
            "password": "alicepassword123",
        },
    )

    assert register_response.status_code == 201

    alice_headers = login(
        username="alice",
        password="alicepassword123",
    )

    response = client.patch(
        f"/users/me/urls/{short_code}",
        json={
            "url": "https://github.com/",
        },
        headers=alice_headers,
    )

    assert response.status_code == 404

    redirect_response = client.get(
        f"/{short_code}",
        follow_redirects=False,
    )

    assert redirect_response.status_code == 307
    assert redirect_response.headers["location"] == "https://example.com/"


def test_user_cannot_delete_another_users_url(
    client: TestClient,
    login,
):
    owner_headers = login()

    create_response = client.post(
        "/urls",
        json={
            "url": "https://example.com/",
        },
        headers=owner_headers,
    )

    short_code = create_response.json()["short_code"]

    register_response = client.post(
        "/users",
        json={
            "username": "alice",
            "password": "alicepassword123",
        },
    )

    assert register_response.status_code == 201

    alice_headers = login(
        username="alice",
        password="alicepassword123",
    )

    response = client.delete(
        f"/users/me/urls/{short_code}",
        headers=alice_headers,
    )

    assert response.status_code == 404

    redirect_response = client.get(
        f"/{short_code}",
        follow_redirects=False,
    )

    assert redirect_response.status_code == 307
    assert redirect_response.headers["location"] == "https://example.com/"


def test_users_only_see_their_own_urls(
    client: TestClient,
    login,
):
    testuser_headers = login()

    client.post(
        "/urls",
        json={
            "url": "https://example.com/",
        },
        headers=testuser_headers,
    )

    register_response = client.post(
        "/users",
        json={
            "username": "alice",
            "password": "alicepassword123",
        },
    )

    assert register_response.status_code == 201

    alice_headers = login(
        username="alice",
        password="alicepassword123",
    )

    client.post(
        "/urls",
        json={
            "url": "https://github.com/",
        },
        headers=alice_headers,
    )

    testuser_urls = client.get(
        "/users/me/urls",
        headers=testuser_headers,
    )

    alice_urls = client.get(
        "/users/me/urls",
        headers=alice_headers,
    )

    assert testuser_urls.status_code == 200
    assert alice_urls.status_code == 200

    testuser_urls_body = testuser_urls.json()
    alice_urls_body = alice_urls.json()

    assert len(testuser_urls_body) == 1
    assert len(alice_urls_body) == 1

    assert testuser_urls_body[0]["original_url"] == "https://example.com/"
    assert alice_urls_body[0]["original_url"] == "https://github.com/"