from datetime import timedelta
from unittest.mock import MagicMock

import boto3
import pytest
from moto import mock_aws

from src.domain.filters import TaskFilter
from src.infrastructure.dynamo_table import GSI_NAME, create_tasks_table
from src.infrastructure.dynamo_task_repository import DynamoTaskRepository
from tests.application.fakes import FixedClock


@pytest.fixture
def table():
    with mock_aws():
        resource = boto3.resource("dynamodb", region_name="us-east-1")
        yield create_tasks_table(resource, "tasks")


@pytest.fixture
def repo(table, now) -> DynamoTaskRepository:
    return DynamoTaskRepository(table, FixedClock(now))


def ids(tasks) -> list[str]:
    return [t.id for t in tasks]


def test_round_trips_every_field(repo, make_task, now):
    task = make_task(
        description="desc",
        actual_time_hours=3,
        tags=["a", "b"],
        type="group-work",
        group_members=["u2"],
        attachments=["x.pdf"],
        completed_at=now,
    )
    repo.save(task)

    assert repo.get("t1") == task


def test_save_upserts(repo, make_task):
    repo.save(make_task(title="old"))
    repo.save(make_task(title="new"))

    assert repo.get("t1").title == "new"


def test_save_moves_task_when_period_or_due_date_change(repo, make_task, now):
    repo.save(make_task(period_id="p1"))
    repo.save(make_task(period_id="p2", due_date=now + timedelta(days=9)))

    old, _ = repo.list(TaskFilter(user_id="u1", period_id="p1"))
    new, _ = repo.list(TaskFilter(user_id="u1", period_id="p2"))

    assert ids(old) == []
    assert ids(new) == ["t1"]


def test_list_with_period_queries_gsi_with_prefix(table, make_task, now):
    spy = MagicMock(wraps=table)
    repo = DynamoTaskRepository(spy, FixedClock(now))
    repo.save(make_task(id="a", period_id="p1"))
    repo.save(make_task(id="b", period_id="p10"))

    items, _ = repo.list(TaskFilter(user_id="u1", period_id="p1"))

    assert ids(items) == ["a"]
    spy.scan.assert_not_called()
    assert spy.query.call_args.kwargs["IndexName"] == GSI_NAME


def test_list_without_period_returns_all_periods(repo, make_task):
    repo.save(make_task(id="a", period_id="p1"))
    repo.save(make_task(id="b", period_id="p2"))

    items, _ = repo.list(TaskFilter(user_id="u1"))

    assert sorted(ids(items)) == ["a", "b"]


def test_follows_pagination_of_the_query(table, make_task, now):
    repo = DynamoTaskRepository(table, FixedClock(now), query_page_size=2)
    for n in range(7):
        repo.save(make_task(id=f"t{n}", due_date=now + timedelta(days=n + 1)))

    listed, page = repo.list(TaskFilter(user_id="u1", limit=100))

    assert len(listed) == 7 and page.total == 7
    assert len(repo.list_all("u1")) == 7
    by_period, _ = repo.list(TaskFilter(user_id="u1", period_id="p1", limit=100))
    assert len(by_period) == 7


def test_period_listing_ignores_other_users(repo, make_task):
    repo.save(make_task(id="a", user_id="u1"))
    repo.save(make_task(id="b", user_id="u2"))

    items, _ = repo.list(TaskFilter(user_id="u1", period_id="p1"))

    assert ids(items) == ["a"]
