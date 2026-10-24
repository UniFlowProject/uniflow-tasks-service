from datetime import timedelta

from src.domain.enums import TaskStatus


def test_create_task_returns_201_with_camel_case_body(client, new_task_body, repo, scheduler):
    response = client.post("/tasks", json=new_task_body)

    assert response.status_code == 201
    body = response.json()
    assert body["id"] == "id-1"
    assert body["userId"] == "u1"
    assert body["status"] == "todo"
    assert body["estimatedTimeHours"] == 4
    assert body["dueDate"].startswith("2026-11-01T10:00:00")
    assert repo.get("id-1") is not None
    assert len(scheduler.scheduled) == 1


def test_get_task_returns_it(client, repo, make_task):
    repo.save(make_task())

    response = client.get("/tasks/t1")

    assert response.status_code == 200
    assert response.json()["title"] == "Homework"


def test_list_tasks_returns_items_and_page_info(client, repo, make_task):
    repo.save(make_task(id="a"))
    repo.save(make_task(id="b", user_id="u2"))

    response = client.get("/tasks")

    assert response.status_code == 200
    body = response.json()
    assert [t["id"] for t in body["items"]] == ["a"]
    assert body["pageInfo"] == {
        "total": 1,
        "page": 1,
        "limit": 20,
        "totalPages": 1,
        "hasNext": False,
        "hasPrev": False,
    }


def test_list_tasks_maps_query_params_to_filter(client, repo, make_task, now):
    repo.save(make_task(id="a", status=TaskStatus.DONE, subject_id="s9"))
    repo.save(make_task(id="b", status=TaskStatus.TODO, subject_id="s9"))
    repo.save(make_task(id="c", status=TaskStatus.IN_PROGRESS, subject_id="s9"))
    repo.save(make_task(id="d", status=TaskStatus.TODO, subject_id="other"))

    response = client.get(
        "/tasks",
        params={
            "status": ["todo", "in-progress"],
            "subjectId": "s9",
            "sortBy": "status",
            "sortOrder": "desc",
            "page": 1,
            "limit": 1,
        },
    )

    body = response.json()
    assert [t["id"] for t in body["items"]] == ["c"]
    assert body["pageInfo"]["total"] == 2
    assert body["pageInfo"]["hasNext"] is True


def test_list_tasks_supports_search_and_due_date_range(client, repo, make_task, now):
    repo.save(make_task(id="a", title="Calculus", due_date=now + timedelta(days=2)))
    repo.save(make_task(id="b", title="Calculus", due_date=now + timedelta(days=20)))

    response = client.get(
        "/tasks",
        params={
            "search": "calc",
            "dueDateTo": (now + timedelta(days=5)).isoformat(),
            "isOverdue": "false",
        },
    )

    assert [t["id"] for t in response.json()["items"]] == ["a"]


def test_list_tasks_rejects_invalid_query_params(client):
    assert client.get("/tasks", params={"limit": 1000}).status_code == 422
    assert client.get("/tasks", params={"status": "bogus"}).status_code == 422
    assert client.get("/tasks", params={"timeZone": "Mars/Base"}).status_code == 422


def test_update_task_applies_partial_changes(client, repo, make_task):
    repo.save(make_task())

    response = client.patch("/tasks/t1", json={"title": "New title", "priority": "urgent"})

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "New title"
    assert body["priority"] == "urgent"
    assert body["subjectId"] == "s1"


def test_change_status_returns_updated_task(client, repo, make_task):
    repo.save(make_task())

    response = client.patch("/tasks/t1/status", json={"status": "in-progress"})

    assert response.status_code == 200
    assert response.json()["status"] == "in-progress"
    assert repo.get("t1").status == TaskStatus.IN_PROGRESS


def test_delete_task_returns_204(client, repo, make_task, scheduler):
    repo.save(make_task())

    response = client.delete("/tasks/t1")

    assert response.status_code == 204
    assert response.content == b""
    assert repo.get("t1") is None
    assert scheduler.cancelled == ["t1"]


def test_stats_endpoint_is_not_shadowed_by_task_id_route(client, repo, make_task):
    repo.save(make_task(id="a", status=TaskStatus.DONE))
    repo.save(make_task(id="b"))

    response = client.get("/tasks/stats")

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 2
    assert body["completed"] == 1
    assert body["pending"] == 1
    assert body["byStatus"] == {"done": 1, "todo": 1}
    assert body["byPriority"] == {"medium": 2}
    assert body["bySubject"] == {"s1": 2}
