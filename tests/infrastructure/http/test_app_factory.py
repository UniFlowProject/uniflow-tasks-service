from fastapi.testclient import TestClient

from src.infrastructure.http.app import create_app
from src.infrastructure.http.headers import USER_ID_HEADER


def test_default_app_works_end_to_end_with_in_memory_adapters(new_task_body):
    client = TestClient(create_app(), headers={USER_ID_HEADER: "u1"})

    created = client.post("/tasks", json=new_task_body).json()
    fetched = client.get(f"/tasks/{created['id']}")

    assert fetched.status_code == 200
    assert fetched.json()["id"] == created["id"]


def test_each_app_gets_its_own_state(new_task_body):
    first = TestClient(create_app(), headers={USER_ID_HEADER: "u1"})
    second = TestClient(create_app(), headers={USER_ID_HEADER: "u1"})
    first.post("/tasks", json=new_task_body)

    assert second.get("/tasks").json()["items"] == []


def test_main_exposes_an_app():
    from main import app

    assert app.title


def test_health_endpoint_reports_ok(anonymous_client):
    response = anonymous_client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
