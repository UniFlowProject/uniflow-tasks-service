from datetime import datetime

from pydantic import BaseModel

from src.application.ports.clock import Clock
from src.application.ports.reminder_scheduler import ReminderScheduler
from src.application.ports.task_repository import TaskRepository
from src.application.reminders import schedule_reminder
from src.application.use_cases.loader import load_owned_task
from src.domain.enums import TaskPriority, TaskType
from src.domain.task import Task
from src.domain.user import UserContext


class UpdateTaskCommand(BaseModel):
    """Partial update: fields left unset stay unchanged. Status has its own use case."""

    title: str | None = None
    description: str | None = None
    subject_id: str | None = None
    period_id: str | None = None
    due_date: datetime | None = None
    priority: TaskPriority | None = None
    type: TaskType | None = None
    estimated_time_hours: int | None = None
    actual_time_hours: int | None = None
    tags: list[str] | None = None
    group_members: list[str] | None = None
    attachments: list[str] | None = None


class UpdateTask:
    def __init__(
        self,
        repository: TaskRepository,
        clock: Clock,
        scheduler: ReminderScheduler,
    ):
        self._repository = repository
        self._clock = clock
        self._scheduler = scheduler

    def execute(self, user: UserContext, task_id: str, command: UpdateTaskCommand) -> Task:
        task = load_owned_task(self._repository, user, task_id)
        changes = command.model_dump(exclude_unset=True)
        updated = task.with_changes(self._clock.now(), **changes)
        self._repository.save(updated)
        if updated.due_date != task.due_date:
            schedule_reminder(self._scheduler, updated)
        return updated
