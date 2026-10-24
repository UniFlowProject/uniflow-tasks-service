from datetime import UTC, datetime, timedelta

import pytest

from src.domain.enums import TaskPriority, TaskStatus, TaskType
from src.domain.task import Task

NOW = datetime(2026, 10, 23, 12, 0, tzinfo=UTC)


@pytest.fixture
def now() -> datetime:
    return NOW


@pytest.fixture
def make_task():
    def _make(**overrides) -> Task:
        data = dict(
            id="t1",
            user_id="u1",
            title="Homework",
            subject_id="s1",
            period_id="p1",
            due_date=NOW + timedelta(days=3),
            status=TaskStatus.TODO,
            priority=TaskPriority.MEDIUM,
            type=TaskType.ASSIGNMENT,
            estimated_time_hours=2,
            created_at=NOW,
            updated_at=NOW,
        )
        data.update(overrides)
        return Task(**data)

    return _make
