from datetime import timedelta

import pytest
from pydantic import ValidationError

from src.domain.enums import TaskStatus, TaskType
from src.domain.error import (
    ForbiddenError,
    InvalidStatusTransitionError,
    TaskNotModifiableError,
)


def test_transition_updates_status_and_timestamp(make_task, now):
    task = make_task()
    later = now + timedelta(hours=1)

    task.transition_to(TaskStatus.IN_PROGRESS, later)

    assert task.status == TaskStatus.IN_PROGRESS
    assert task.updated_at == later
    assert task.completed_at is None


def test_transition_to_done_sets_completed_at(make_task, now):
    task = make_task(status=TaskStatus.IN_REVIEW)

    task.transition_to(TaskStatus.DONE, now)

    assert task.completed_at == now


@pytest.mark.parametrize("final", [TaskStatus.DONE, TaskStatus.CANCELLED])
def test_final_states_cannot_transition(make_task, now, final):
    task = make_task(status=final)

    with pytest.raises(InvalidStatusTransitionError):
        task.transition_to(TaskStatus.IN_PROGRESS, now)


def test_todo_cannot_jump_to_done(make_task, now):
    with pytest.raises(InvalidStatusTransitionError):
        make_task().transition_to(TaskStatus.DONE, now)


def test_same_status_is_invalid_transition(make_task, now):
    with pytest.raises(InvalidStatusTransitionError):
        make_task().transition_to(TaskStatus.TODO, now)


def test_ensure_modifiable_rejects_final_states(make_task):
    with pytest.raises(TaskNotModifiableError):
        make_task(status=TaskStatus.DONE).ensure_modifiable()


def test_ensure_owned_by(make_task):
    task = make_task()
    task.ensure_owned_by("u1")
    with pytest.raises(ForbiddenError):
        task.ensure_owned_by("someone-else")


def test_group_members_require_group_work(make_task):
    with pytest.raises(ValidationError):
        make_task(group_members=["u2"], type=TaskType.ASSIGNMENT)
    make_task(group_members=["u2"], type=TaskType.GROUP_WORK)


@pytest.mark.parametrize("field", ["estimated_time_hours", "actual_time_hours"])
def test_hours_cannot_be_negative(make_task, field):
    with pytest.raises(ValidationError):
        make_task(**{field: -1})


def test_is_overdue(make_task, now):
    past = make_task(due_date=now - timedelta(hours=1))
    assert past.is_overdue(now)
    assert not make_task().is_overdue(now)
    assert not make_task(due_date=now - timedelta(hours=1), status=TaskStatus.DONE).is_overdue(now)


def test_is_due_soon_within_24h(make_task, now):
    assert make_task(due_date=now + timedelta(hours=5)).is_due_soon(now)
    assert not make_task(due_date=now + timedelta(hours=30)).is_due_soon(now)
    assert not make_task(due_date=now - timedelta(hours=1)).is_due_soon(now)
