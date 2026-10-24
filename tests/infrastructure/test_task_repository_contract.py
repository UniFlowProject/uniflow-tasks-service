from datetime import timedelta

import boto3
import pytest
from moto import mock_aws

from src.domain.enums import SortOrder, TaskPriority, TaskSortField, TaskStatus
from src.domain.filters import TaskFilter
from src.infrastructure.dynamo_table import create_tasks_table
from src.infrastructure.dynamo_task_repository import DynamoTaskRepository
from src.infrastructure.in_memory_task_repository import InMemoryTaskRepository
from tests.application.fakes import FixedClock


@pytest.fixture(params=["memory", "dynamodb"])
def repo(request, now):
    clock = FixedClock(now)
    if request.param == "memory":
        yield InMemoryTaskRepository(clock)
        return
    with mock_aws():
        resource = boto3.resource("dynamodb", region_name="us-east-1")
        yield DynamoTaskRepository(create_tasks_table(resource, "tasks"), clock)


def ids(tasks) -> list[str]:
    return [t.id for t in tasks]


def test_save_then_get_returns_task(repo, make_task):
    task = make_task()
    repo.save(task)

    assert repo.get("t1") == task


def test_get_unknown_returns_none(repo):
    assert repo.get("missing") is None


def test_delete_removes_task_and_ignores_unknown(repo, make_task):
    repo.save(make_task())

    repo.delete("t1")
    repo.delete("t1")

    assert repo.get("t1") is None


def test_list_all_returns_only_tasks_of_user(repo, make_task):
    repo.save(make_task(id="a", user_id="u1"))
    repo.save(make_task(id="b", user_id="u2"))

    assert ids(repo.list_all("u1")) == ["a"]


def test_list_scopes_to_user(repo, make_task):
    repo.save(make_task(id="a", user_id="u1"))
    repo.save(make_task(id="b", user_id="u2"))

    items, page = repo.list(TaskFilter(user_id="u1"))

    assert ids(items) == ["a"]
    assert page.total == 1


def test_list_filters_by_status_and_priority(repo, make_task):
    repo.save(make_task(id="a", status=TaskStatus.DONE))
    repo.save(make_task(id="b", priority=TaskPriority.HIGH))
    repo.save(make_task(id="c"))

    by_status, _ = repo.list(TaskFilter(user_id="u1", status=[TaskStatus.DONE]))
    by_priority, _ = repo.list(TaskFilter(user_id="u1", priority=[TaskPriority.HIGH]))

    assert ids(by_status) == ["a"]
    assert ids(by_priority) == ["b"]


def test_list_treats_empty_status_and_priority_as_no_filter(repo, make_task):
    repo.save(make_task(id="a", status=TaskStatus.DONE))
    repo.save(make_task(id="b", priority=TaskPriority.HIGH))

    found, _ = repo.list(TaskFilter(user_id="u1", status=[], priority=[]))

    assert sorted(ids(found)) == ["a", "b"]


def test_list_filters_by_subject_and_period(repo, make_task):
    repo.save(make_task(id="a", subject_id="s2"))
    repo.save(make_task(id="b", period_id="p2"))
    repo.save(make_task(id="c"))

    by_subject, _ = repo.list(TaskFilter(user_id="u1", subject_id="s2"))
    by_period, _ = repo.list(TaskFilter(user_id="u1", period_id="p2"))

    assert ids(by_subject) == ["a"]
    assert ids(by_period) == ["b"]


def test_list_filters_by_due_date_range(repo, make_task, now):
    repo.save(make_task(id="early", due_date=now + timedelta(days=1)))
    repo.save(make_task(id="mid", due_date=now + timedelta(days=5)))
    repo.save(make_task(id="late", due_date=now + timedelta(days=9)))

    items, _ = repo.list(
        TaskFilter(
            user_id="u1",
            due_date_from=now + timedelta(days=2),
            due_date_to=now + timedelta(days=6),
        )
    )

    assert ids(items) == ["mid"]


def test_list_filters_overdue_using_clock(repo, make_task, now):
    repo.save(make_task(id="late", due_date=now - timedelta(days=1)))
    repo.save(make_task(id="ok", due_date=now + timedelta(days=1)))
    repo.save(
        make_task(id="done", due_date=now - timedelta(days=1), status=TaskStatus.DONE)
    )

    overdue, _ = repo.list(TaskFilter(user_id="u1", is_overdue=True))
    not_overdue, _ = repo.list(TaskFilter(user_id="u1", is_overdue=False))

    assert ids(overdue) == ["late"]
    assert sorted(ids(not_overdue)) == ["done", "ok"]


def test_list_filters_due_soon_using_clock(repo, make_task, now):
    repo.save(make_task(id="soon", due_date=now + timedelta(hours=3)))
    repo.save(make_task(id="far", due_date=now + timedelta(days=3)))

    items, _ = repo.list(TaskFilter(user_id="u1", is_due_soon=True))

    assert ids(items) == ["soon"]


def test_list_search_matches_title_or_description_case_insensitive(repo, make_task):
    repo.save(make_task(id="a", title="Calculus HOMEWORK"))
    repo.save(make_task(id="b", title="Other", description="some homework here"))
    repo.save(make_task(id="c", title="Unrelated"))

    items, _ = repo.list(TaskFilter(user_id="u1", search="homework"))

    assert sorted(ids(items)) == ["a", "b"]


def test_list_sorts_by_due_date_ascending_by_default(repo, make_task, now):
    repo.save(make_task(id="b", due_date=now + timedelta(days=2)))
    repo.save(make_task(id="a", due_date=now + timedelta(days=1)))

    items, _ = repo.list(TaskFilter(user_id="u1"))

    assert ids(items) == ["a", "b"]


def test_list_sorts_by_priority_by_rank_descending(repo, make_task):
    repo.save(make_task(id="low", priority=TaskPriority.LOW))
    repo.save(make_task(id="urgent", priority=TaskPriority.URGENT))
    repo.save(make_task(id="high", priority=TaskPriority.HIGH))

    items, _ = repo.list(
        TaskFilter(
            user_id="u1", sort_by=TaskSortField.PRIORITY, sort_order=SortOrder.DESC
        )
    )

    assert ids(items) == ["urgent", "high", "low"]


def test_list_sorts_by_created_at(repo, make_task, now):
    repo.save(make_task(id="new", created_at=now + timedelta(hours=1)))
    repo.save(make_task(id="old", created_at=now))

    items, _ = repo.list(
        TaskFilter(user_id="u1", sort_by=TaskSortField.CREATED_AT, sort_order=SortOrder.DESC)
    )

    assert ids(items) == ["new", "old"]


def test_list_sorts_by_status_by_workflow_order(repo, make_task):
    repo.save(make_task(id="done", status=TaskStatus.DONE))
    repo.save(make_task(id="todo", status=TaskStatus.TODO))
    repo.save(make_task(id="review", status=TaskStatus.IN_REVIEW))

    items, _ = repo.list(TaskFilter(user_id="u1", sort_by=TaskSortField.STATUS))

    assert ids(items) == ["todo", "review", "done"]


def test_list_paginates_after_filtering_and_sorting(repo, make_task, now):
    for n in range(5):
        repo.save(make_task(id=f"t{n}", due_date=now + timedelta(days=n + 1)))

    items, page = repo.list(TaskFilter(user_id="u1", page=2, limit=2))

    assert ids(items) == ["t2", "t3"]
    assert (page.total, page.total_pages, page.has_next, page.has_prev) == (5, 3, True, True)
