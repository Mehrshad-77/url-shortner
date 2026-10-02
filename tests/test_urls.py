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
    authenticated_client: TestClient,
):
    response = authenticated_client.post(
        "/urls",
        json={
            "url": "https://example.com/",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert "id" in body
    assert "short_code" in body
    assert body["username"] == "testuser"

    assert len(body["short_code"]) == 7


def test_create_url_with_invalid_url(
    authenticated_client: TestClient,
):
    response = authenticated_client.post(
        "/urls",
        json={
            "url": "not-a-valid-url",
        },
    )

    assert response.status_code == 422


def test_duplicate_url_returns_409(
    authenticated_client: TestClient,
):
    first_response = authenticated_client.post(
        "/urls",
        json={
            "url": "https://example.com/",
        },
    )

    assert first_response.status_code == 200

    second_response = authenticated_client.post(
        "/urls",
        json={
            "url": "https://example.com/",
        },
    )

    assert second_response.status_code == 409

    assert second_response.json() == {
        "detail": "URL already exists"
    }


def test_redirect_url(
    authenticated_client: TestClient,
):
    create_response = authenticated_client.post(
        "/urls",
        json={
            "url": "https://github.com/",
        },
    )

    assert create_response.status_code == 200

    short_code = create_response.json()["short_code"]

    response = authenticated_client.get(
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
    authenticated_client: TestClient,
):
    authenticated_client.post(
        "/urls",
        json={
            "url": "https://example.com/",
        },
    )

    authenticated_client.post(
        "/urls",
        json={
            "url": "https://github.com/",
        },
    )

    response = authenticated_client.get(
        "/users/me/urls",
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body) == 2

    assert body[0]["original_url"] == "https://example.com/"
    assert body[1]["original_url"] == "https://github.com/"


def test_get_my_urls_pagination(
    authenticated_client: TestClient,
):
    urls = [
        "https://example.com/",
        "https://github.com/",
        "https://openai.com/",
        "https://fastapi.tiangolo.com/",
    ]

    for url in urls:
        response = authenticated_client.post(
            "/urls",
            json={"url": url},
        )

        assert response.status_code == 200

    first_page = authenticated_client.get(
        "/users/me/urls?skip=0&limit=2",
    )

    assert first_page.status_code == 200

    first_body = first_page.json()

    assert len(first_body) == 2
    assert first_body[0]["original_url"] == urls[0]
    assert first_body[1]["original_url"] == urls[1]

    second_page = authenticated_client.get(
        "/users/me/urls?skip=2&limit=2",
    )

    assert second_page.status_code == 200

    second_body = second_page.json()

    assert len(second_body) == 2
    assert second_body[0]["original_url"] == urls[2]
    assert second_body[1]["original_url"] == urls[3]


def test_get_my_urls_limit_validation(
    authenticated_client: TestClient,
):
    response = authenticated_client.get(
        "/users/me/urls?limit=101",
    )

    assert response.status_code == 422


def test_update_own_url(
    authenticated_client: TestClient,
):
    create_response = authenticated_client.post(
        "/urls",
        json={
            "url": "https://example.com/",
        },
    )

    short_code = create_response.json()["short_code"]

    update_response = authenticated_client.patch(
        f"/users/me/urls/{short_code}",
        json={
            "url": "https://github.com/",
        },
    )

    assert update_response.status_code == 200

    body = update_response.json()

    assert body["original_url"] == "https://github.com/"
    assert body["short_code"] == short_code


def test_update_invalid_url(
    authenticated_client: TestClient,
):
    create_response = authenticated_client.post(
        "/urls",
        json={
            "url": "https://example.com/",
        },
    )

    short_code = create_response.json()["short_code"]

    response = authenticated_client.patch(
        f"/users/me/urls/{short_code}",
        json={
            "url": "not-a-valid-url",
        },
    )

    assert response.status_code == 422


def test_update_missing_url_returns_404(
    authenticated_client: TestClient,
):
    response = authenticated_client.patch(
        "/users/me/urls/doesnotexist",
        json={
            "url": "https://github.com/",
        },
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "URL not found"
    }


def test_delete_own_url(
    authenticated_client: TestClient,
):
    create_response = authenticated_client.post(
        "/urls",
        json={
            "url": "https://example.com/",
        },
    )

    short_code = create_response.json()["short_code"]

    delete_response = authenticated_client.delete(
        f"/users/me/urls/{short_code}",
    )

    assert delete_response.status_code == 204

    redirect_response = authenticated_client.get(
        f"/{short_code}",
        follow_redirects=False,
    )

    assert redirect_response.status_code == 404


def test_delete_missing_url_returns_404(
    authenticated_client: TestClient,
):
    response = authenticated_client.delete(
        "/users/me/urls/doesnotexist",
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "URL not found"
    }


def test_user_cannot_update_another_users_url(
    client: TestClient,
    login,
    alice_user,
    alice_password
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

    alice_headers = login(
        username=alice_user.username,
        password=alice_password,
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
    alice_user,
    alice_password
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

    alice_headers = login(
        username=alice_user.username,
        password=alice_password,
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
    alice_user,
    alice_password
):
    testuser_headers = login()

    client.post(
        "/urls",
        json={
            "url": "https://example.com/",
        },
        headers=testuser_headers,
    )

    alice_headers = login(
        username=alice_user.username,
        password=alice_password,
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

def test_duplicate_url_across_users_returns_409(
    client: TestClient,
    login,
    alice_user,
    alice_password,
):
    testuser_headers = login()

    first_response = client.post(
        "/urls",
        json={
            "url": "https://example.com/",
        },
        headers=testuser_headers,
    )

    assert first_response.status_code == 200

    alice_headers = login(
        username=alice_user.username,
        password=alice_password,
    )

    second_response = client.post(
        "/urls",
        json={
            "url": "https://example.com/",
        },
        headers=alice_headers,
    )

    assert second_response.status_code == 409

    assert second_response.json() == {
        "detail": "URL already exists"
    }

def test_update_url_to_existing_url_returns_409(
    authenticated_client: TestClient,
):
    first_response = authenticated_client.post(
        "/urls",
        json={
            "url": "https://example.com/",
        },
    )

    assert first_response.status_code == 200

    second_response = authenticated_client.post(
        "/urls",
        json={
            "url": "https://github.com/",
        },
    )

    assert second_response.status_code == 200

    first_short_code = first_response.json()["short_code"]

    update_response = authenticated_client.patch(
        f"/users/me/urls/{first_short_code}",
        json={
            "url": "https://github.com/",
        },
    )

    assert update_response.status_code == 409

    assert update_response.json() == {
        "detail": "URL already exists"
    }

def test_get_my_urls_skip_beyond_results(
    authenticated_client: TestClient,
):
    response = authenticated_client.post(
        "/urls",
        json={
            "url": "https://example.com/",
        },
    )

    assert response.status_code == 200

    response = authenticated_client.get(
        "/users/me/urls?skip=10&limit=10",
    )

    assert response.status_code == 200
    assert response.json() == []

def test_get_my_urls_negative_skip(
    authenticated_client: TestClient,
):
    response = authenticated_client.get(
        "/users/me/urls?skip=-1",
    )

    assert response.status_code == 422

def test_update_url_to_same_url_returns_400(
    authenticated_client: TestClient,
):
    create_response = authenticated_client.post(
        "/urls",
        json={
            "url": "https://example.com/",
        },
    )

    assert create_response.status_code == 200

    short_code = create_response.json()["short_code"]

    update_response = authenticated_client.patch(
        f"/users/me/urls/{short_code}",
        json={
            "url": "https://example.com/",
        },
    )

    assert update_response.status_code == 400

    assert update_response.json() == {
        "detail": "The new URL is the same as the current one"
    }

def test_redirect_url_does_not_require_authentication(
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

    assert create_response.status_code == 200

    short_code = create_response.json()["short_code"]

    response = client.get(
        f"/{short_code}",
        follow_redirects=False,
    )

    assert response.status_code == 307
    assert response.headers["location"] == "https://example.com/"

def test_short_code_contains_only_base62_characters(
    authenticated_client: TestClient,
):
    response = authenticated_client.post(
        "/urls",
        json={
            "url": "https://example.com/",
        },
    )

    assert response.status_code == 200

    short_code = response.json()["short_code"]

    assert len(short_code) == 7
    assert all(
        character in "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
        for character in short_code
    )

def test_short_codes_are_unique(
    authenticated_client: TestClient,
):
    first_response = authenticated_client.post(
        "/urls",
        json={"url": "https://example.com/"},
    )
    assert first_response.status_code == 200

    second_response = authenticated_client.post(
        "/urls",
        json={"url": "https://github.com/"},
    )
    assert second_response.status_code == 200

    first_short_code = first_response.json()["short_code"]
    second_short_code = second_response.json()["short_code"]

    assert first_short_code != second_short_code

def test_create_url_response_contains_expected_fields(
    authenticated_client: TestClient,
):
    response = authenticated_client.post(
        "/urls",
        json={
            "url": "https://example.com/",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert "id" in body
    assert "short_code" in body
    assert "username" in body

    assert isinstance(body["id"], int)
    assert isinstance(body["short_code"], str)
    assert body["username"] == "testuser"


def test_create_url_does_not_expose_password(
    authenticated_client: TestClient,
):
    response = authenticated_client.post(
        "/urls",
        json={
            "url": "https://example.com/",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert "password" not in body
    assert "hashed_password" not in body

def test_user_cannot_access_another_users_url_by_short_code(
    client: TestClient,
    login,
    alice_user,
    alice_password,
):
    testuser_headers = login()

    create_response = client.post(
        "/urls",
        json={
            "url": "https://example.com/",
        },
        headers=testuser_headers,
    )

    assert create_response.status_code == 200

    short_code = create_response.json()["short_code"]

    alice_headers = login(
        username=alice_user.username,
        password=alice_password,
    )

    response = client.patch(
        f"/users/me/urls/{short_code}",
        json={
            "url": "https://github.com/",
        },
        headers=alice_headers,
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "URL not found"
    }


def test_user_cannot_delete_another_users_url_by_short_code(
    client: TestClient,
    login,
    alice_user,
    alice_password,
):
    testuser_headers = login()

    create_response = client.post(
        "/urls",
        json={
            "url": "https://example.com/",
        },
        headers=testuser_headers,
    )

    assert create_response.status_code == 200

    short_code = create_response.json()["short_code"]

    alice_headers = login(
        username=alice_user.username,
        password=alice_password,
    )

    response = client.delete(
        f"/users/me/urls/{short_code}",
        headers=alice_headers,
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "URL not found"
    }

def test_get_my_urls_respects_limit(
    authenticated_client: TestClient,
):
    urls = [
        "https://example.com/",
        "https://github.com/",
        "https://google.com/",
    ]

    for url in urls:
        response = authenticated_client.post(
            "/urls",
            json={"url": url},
        )
        assert response.status_code == 200

    response = authenticated_client.get(
        "/users/me/urls?limit=2"
    )

    assert response.status_code == 200
    assert len(response.json()) == 2


def test_get_my_urls_respects_skip_and_limit(
    authenticated_client: TestClient,
):
    urls = [
        "https://example.com/",
        "https://github.com/",
        "https://google.com/",
    ]

    for url in urls:
        response = authenticated_client.post(
            "/urls",
            json={"url": url},
        )
        assert response.status_code == 200

    response = authenticated_client.get(
        "/users/me/urls?skip=1&limit=1"
    )

    assert response.status_code == 200
    assert len(response.json()) == 1

def test_get_my_urls_zero_limit(
    authenticated_client: TestClient,
):
    response = authenticated_client.get(
        "/users/me/urls?limit=0"
    )

    assert response.status_code == 422


def test_get_my_urls_limit_above_maximum(
    authenticated_client: TestClient,
):
    response = authenticated_client.get(
        "/users/me/urls?limit=101"
    )

    assert response.status_code == 422

def test_update_url_changes_original_url(
    authenticated_client: TestClient,
):
    create_response = authenticated_client.post(
        "/urls",
        json={
            "url": "https://example.com/",
        },
    )

    assert create_response.status_code == 200

    short_code = create_response.json()["short_code"]

    update_response = authenticated_client.patch(
        f"/users/me/urls/{short_code}",
        json={
            "url": "https://github.com/",
        },
    )

    assert update_response.status_code == 200

    body = update_response.json()

    assert body["short_code"] == short_code


def test_updated_url_redirects_to_new_destination(
    authenticated_client: TestClient,
    client: TestClient,
):
    create_response = authenticated_client.post(
        "/urls",
        json={
            "url": "https://example.com/",
        },
    )

    assert create_response.status_code == 200

    short_code = create_response.json()["short_code"]

    update_response = authenticated_client.patch(
        f"/users/me/urls/{short_code}",
        json={
            "url": "https://github.com/",
        },
    )

    assert update_response.status_code == 200

    redirect_response = client.get(
        f"/{short_code}",
        follow_redirects=False,
    )

    assert redirect_response.status_code == 307
    assert redirect_response.headers["location"] == "https://github.com/"

def test_deleted_url_cannot_be_redirected(
    authenticated_client: TestClient,
    client: TestClient,
):
    create_response = authenticated_client.post(
        "/urls",
        json={
            "url": "https://example.com/",
        },
    )

    assert create_response.status_code == 200

    short_code = create_response.json()["short_code"]

    delete_response = authenticated_client.delete(
        f"/users/me/urls/{short_code}"
    )

    assert delete_response.status_code == 204

    redirect_response = client.get(
        f"/{short_code}",
        follow_redirects=False,
    )

    assert redirect_response.status_code == 404
    assert redirect_response.json() == {
        "detail": "URL not found"
    }

def test_get_my_urls_returns_empty_list_for_new_user(
    authenticated_client: TestClient,
):
    response = authenticated_client.get(
        "/users/me/urls"
    )

    assert response.status_code == 200
    assert response.json() == []

def test_short_code_collision_is_handled(
    authenticated_client: TestClient,
    monkeypatch,
):
    generated_codes = iter(
        [
            "ABC1234",
            "XYZ5678",
        ]
    )

    def fake_generate_short_code(length=7):
        return next(generated_codes)

    from app.services import url_service

    monkeypatch.setattr(
        url_service,
        "generate_short_code",
        fake_generate_short_code,
    )

    first_response = authenticated_client.post(
        "/urls",
        json={
            "url": "https://example.com/",
        },
    )

    assert first_response.status_code == 200
    assert first_response.json()["short_code"] == "ABC1234"

    second_response = authenticated_client.post(
        "/urls",
        json={
            "url": "https://github.com/",
        },
    )

    assert second_response.status_code == 200
    assert second_response.json()["short_code"] == "XYZ5678"