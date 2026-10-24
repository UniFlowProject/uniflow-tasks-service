import pytest

from src.infrastructure.http.headers import (
    USER_EMAIL_HEADER,
    USER_ID_HEADER,
    USER_NAME_HEADER,
    USER_PICTURE_HEADER,
)

PROTECTED = [
    ("POST", "/tasks"),
    ("GET", "/tasks"),
    ("GET", "/tasks/stats"),
    ("GET", "/tasks/t1"),
    ("PATCH", "/tasks/t1"),
    ("PATCH", "/tasks/t1/status"),
    ("DELETE", "/tasks/t1"),
]


@pytest.mark.parametrize(("method", "path"), PROTECTED)
def test_missing_user_header_is_unauthorized(anonymous_client, method, path):
    response = anonymous_client.request(method, path, json={})

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


@pytest.mark.parametrize("value", ["", "   "])
def test_blank_user_id_is_unauthorized(anonymous_client, value):
    response = anonymous_client.get("/tasks", headers={USER_ID_HEADER: value})

    assert response.status_code == 401


def test_optional_profile_headers_are_accepted(anonymous_client):
    response = anonymous_client.get(
        "/tasks",
        headers={
            USER_ID_HEADER: "u1",
            USER_EMAIL_HEADER: "ana@example.com",
            USER_NAME_HEADER: "Ana",
            USER_PICTURE_HEADER: "https://example.com/a.png",
        },
    )

    assert response.status_code == 200


def test_header_names_are_the_gateway_contract():
    assert USER_ID_HEADER == "X-User-Id"
    assert USER_EMAIL_HEADER == "X-User-Email"
    assert USER_NAME_HEADER == "X-User-Name"
    assert USER_PICTURE_HEADER == "X-User-Picture"
