import pytest

from src.domain.enums import TaskStatus
from src.infrastructure.http.dependencies import provide_create_task


def error_of(response) -> dict:
    return response.json()["error"]


def test_unknown_task_is_404(client):
    response = client.get("/tasks/missing")

    assert response.status_code == 404
    assert error_of(response)["code"] == "TASK_NOT_FOUND"
    assert "missing" in error_of(response)["message"]


def test_other_users_task_is_403(client, repo, make_task):
    repo.save(make_task(user_id="u2"))

    response = client.get("/tasks/t1")

    assert response.status_code == 403
    assert error_of(response)["code"] == "FORBIDDEN"


@pytest.mark.parametrize("status", [TaskStatus.DONE, TaskStatus.CANCELLED])
def test_modifying_closed_task_is_409(client, repo, make_task, status):
    repo.save(make_task(status=status))

    response = client.patch("/tasks/t1", json={"title": "x"})

    assert response.status_code == 409
    assert error_of(response)["code"] == "TASK_NOT_MODIFIABLE"


def test_deleting_closed_task_is_409(client, repo, make_task):
    repo.save(make_task(status=TaskStatus.DONE))

    response = client.delete("/tasks/t1")

    assert response.status_code == 409
    assert error_of(response)["code"] == "TASK_NOT_MODIFIABLE"


def test_invalid_status_transition_is_409(client, repo, make_task):
    repo.save(make_task())

    response = client.patch("/tasks/t1/status", json={"status": "done"})

    assert response.status_code == 409
    assert error_of(response)["code"] == "INVALID_STATUS_TRANSITION"


def test_invalid_request_body_is_422_with_details(client, new_task_body):
    del new_task_body["title"]

    response = client.post("/tasks", json=new_task_body)

    assert response.status_code == 422
    assert error_of(response)["code"] == "VALIDATION_ERROR"
    assert any("title" in detail["field"] for detail in error_of(response)["details"])


def test_blank_title_and_negative_hours_are_422(client, new_task_body):
    assert client.post("/tasks", json={**new_task_body, "title": ""}).status_code == 422
    body = {**new_task_body, "estimatedTimeHours": -1}
    assert client.post("/tasks", json=body).status_code == 422


def test_domain_invariant_violation_on_update_is_422(client, repo, make_task):
    repo.save(make_task())

    response = client.patch("/tasks/t1", json={"groupMembers": ["u2"]})

    assert response.status_code == 422
    assert error_of(response)["code"] == "VALIDATION_ERROR"


def test_domain_invariant_violation_on_create_is_422(client, new_task_body):
    response = client.post("/tasks", json={**new_task_body, "groupMembers": ["u2"]})

    assert response.status_code == 422


def test_unknown_route_uses_the_same_error_shape(client):
    response = client.get("/nope")

    assert response.status_code == 404
    assert error_of(response)["code"] == "NOT_FOUND"


def test_unexpected_error_is_500_without_leaking_internals(app, client, new_task_body):
    class Exploding:
        def execute(self, *_):
            raise RuntimeError("db password is hunter2")

    app.dependency_overrides[provide_create_task] = lambda: Exploding()

    response = client.post("/tasks", json=new_task_body)

    assert response.status_code == 500
    assert error_of(response) == {
        "code": "INTERNAL_ERROR",
        "message": "Internal server error",
    }
    assert "hunter2" not in response.text
