from datetime import datetime

from pydantic import BaseModel, Field

from src.application.ports.clock import Clock
from src.application.ports.id_generator import IdGenerator
from src.application.ports.reminder_scheduler import ReminderScheduler
from src.application.ports.task_repository import TaskRepository
from src.application.reminders import schedule_reminder
from src.domain.enums import TaskPriority, TaskStatus, TaskType
from src.domain.task import Task
from src.domain.user import UserContext


class CreateTaskCommand(BaseModel):
    title: str
    description: str = ""
    subject_id: str
    period_id: str
    due_date: datetime
    priority: TaskPriority
    type: TaskType
    estimated_time_hours: int
    tags: list[str] = Field(default_factory=list)
    group_members: list[str] = Field(default_factory=list)
    attachments: list[str] = Field(default_factory=list)


class CreateTask:
    def __init__(
        self,
        repository: TaskRepository,
        clock: Clock,
        scheduler: ReminderScheduler,
        ids: IdGenerator,
    ):
        self._repository = repository
        self._clock = clock
        self._scheduler = scheduler
        self._ids = ids

    def execute(self, user: UserContext, command: CreateTaskCommand) -> Task:
        now = self._clock.now()
        task = Task(
            **command.model_dump(),
            id=self._ids.new_id(),
            user_id=user.id,
            status=TaskStatus.TODO,
            created_at=now,
            updated_at=now,
        )
        self._repository.save(task)
        schedule_reminder(self._scheduler, task)
        return task
