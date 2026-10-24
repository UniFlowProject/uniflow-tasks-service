from datetime import timedelta

import pytest

from src.application.use_cases.change_task_status import ChangeTaskStatus, ChangeTaskStatusCommand
from src.application.use_cases.create_task import CreateTask, CreateTaskCommand
from src.application.use_cases.delete_task import DeleteTask
from src.application.use_cases.get_task import GetTask
from src.application.use_cases.get_task_stats import GetTaskStats
from src.application.use_cases.list_tasks import ListTasks
from src.application.use_cases.update_task import UpdateTask, UpdateTaskCommand
from src.domain.enums import TaskPriority, TaskStatus, TaskType
from src.domain.error import (
    ForbiddenError,
    InvalidStatusTransitionError,
    TaskNotFoundError,
    TaskNotModifiableError,
)
from src.domain.filters import TaskFilter
from tests.application.fakes import RecordingScheduler


def create_command(now, **overrides) -> CreateTaskCommand:
    data = dict(
        title="Essay",
        subject_id="s1",
        period_id="p1",
        due_date=now + timedelta(days=2),
        priority=TaskPriority.HIGH,
        type=TaskType.ESSAY,
        estimated_time_hours=3,
    )
    data.update(overrides)
    return CreateTaskCommand(**data)


# --- CreateTask ---------------------------------------------------------


def test_create_task_persists_and_schedules_reminder(repo, clock, scheduler, ids, user, now):
    use_case = CreateTask(repo, clock, scheduler, ids)

    task = use_case.execute(user, create_command(now))

    assert task.id == "id-1"
    assert task.user_id == "u1"
    assert task.status == TaskStatus.TODO
    assert task.created_at == task.updated_at == now
    assert repo.get("id-1") == task
    assert scheduler.scheduled == [task]


def test_create_task_survives_scheduler_failure(repo, clock, ids, user, now):
    use_case = CreateTask(repo, clock, RecordingScheduler(fail=True), ids)

    task = use_case.execute(user, create_command(now))

    assert repo.get(task.id) is not None


# --- GetTask ------------------------------------------------------------


def test_get_task(repo, user):
    assert GetTask(repo).execute(user, "t1").id == "t1"


def test_get_task_not_found(repo, user):
    with pytest.raises(TaskNotFoundError):
        GetTask(repo).execute(user, "missing")


def test_get_task_of_another_user_is_forbidden(repo, other_user):
    with pytest.raises(ForbiddenError):
        GetTask(repo).execute(other_user, "t1")


# --- UpdateTask ---------------------------------------------------------


def test_update_task_changes_only_given_fields(repo, clock, scheduler, user, now):
    later_clock = clock
    updated = UpdateTask(repo, later_clock, scheduler).execute(
        user, "t1", UpdateTaskCommand(title="Renamed")
    )

    assert updated.title == "Renamed"
    assert updated.subject_id == "s1"
    assert repo.get("t1") == updated
    assert scheduler.scheduled == []


def test_update_task_reschedules_reminder_when_due_date_changes(repo, clock, scheduler, user, now):
    new_due = now + timedelta(days=10)

    updated = UpdateTask(repo, clock, scheduler).execute(
        user, "t1", UpdateTaskCommand(due_date=new_due)
    )

    assert scheduler.scheduled == [updated]


def test_update_task_rejects_final_state(make_task, clock, scheduler, user):
    from tests.application.fakes import InMemoryTaskRepository

    repo = InMemoryTaskRepository(make_task(status=TaskStatus.DONE))
    with pytest.raises(TaskNotModifiableError):
        UpdateTask(repo, clock, scheduler).execute(user, "t1", UpdateTaskCommand(title="x"))


def test_update_task_of_another_user_is_forbidden(repo, clock, scheduler, other_user):
    with pytest.raises(ForbiddenError):
        UpdateTask(repo, clock, scheduler).execute(other_user, "t1", UpdateTaskCommand(title="x"))


# --- ChangeTaskStatus ---------------------------------------------------


def test_change_status_transitions_and_saves(repo, clock, scheduler, user):
    task = ChangeTaskStatus(repo, clock, scheduler).execute(
        user, "t1", ChangeTaskStatusCommand(status=TaskStatus.IN_PROGRESS)
    )

    assert task.status == TaskStatus.IN_PROGRESS
    assert repo.get("t1").status == TaskStatus.IN_PROGRESS
    assert scheduler.cancelled == []


def test_change_status_to_cancelled_cancels_reminder(repo, clock, scheduler, user):
    ChangeTaskStatus(repo, clock, scheduler).execute(
        user, "t1", ChangeTaskStatusCommand(status=TaskStatus.CANCELLED)
    )

    assert scheduler.cancelled == ["t1"]


def test_change_status_invalid_transition(repo, clock, scheduler, user):
    with pytest.raises(InvalidStatusTransitionError):
        ChangeTaskStatus(repo, clock, scheduler).execute(
            user, "t1", ChangeTaskStatusCommand(status=TaskStatus.DONE)
        )
    assert repo.get("t1").status == TaskStatus.TODO


def test_change_status_of_another_user_is_forbidden(repo, clock, scheduler, other_user):
    with pytest.raises(ForbiddenError):
        ChangeTaskStatus(repo, clock, scheduler).execute(
            other_user, "t1", ChangeTaskStatusCommand(status=TaskStatus.IN_PROGRESS)
        )


# --- DeleteTask ---------------------------------------------------------


def test_delete_task_removes_it_and_cancels_reminder(repo, scheduler, user):
    DeleteTask(repo, scheduler).execute(user, "t1")

    assert repo.get("t1") is None
    assert scheduler.cancelled == ["t1"]


def test_delete_finished_task_is_rejected(make_task, scheduler, user):
    from tests.application.fakes import InMemoryTaskRepository

    repo = InMemoryTaskRepository(make_task(status=TaskStatus.CANCELLED))
    with pytest.raises(TaskNotModifiableError):
        DeleteTask(repo, scheduler).execute(user, "t1")


def test_delete_task_of_another_user_is_forbidden(repo, scheduler, other_user):
    with pytest.raises(ForbiddenError):
        DeleteTask(repo, scheduler).execute(other_user, "t1")


# --- ListTasks / GetTaskStats ------------------------------------------


def test_list_tasks_returns_page(repo, user):
    page = ListTasks(repo).execute(TaskFilter(user_id=user.id))

    assert [t.id for t in page.items] == ["t1"]
    assert page.page_info.total == 1


def test_get_task_stats(repo, clock, user):
    stats = GetTaskStats(repo, clock).execute(user)

    assert stats.total == 1
    assert stats.pending == 1
