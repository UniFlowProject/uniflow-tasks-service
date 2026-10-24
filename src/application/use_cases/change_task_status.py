from pydantic import BaseModel

from src.application.ports.clock import Clock
from src.application.ports.reminder_scheduler import ReminderScheduler
from src.application.ports.task_repository import TaskRepository
from src.application.reminders import cancel_reminder
from src.application.use_cases.loader import load_owned_task
from src.domain.enums import TaskStatus
from src.domain.task import Task
from src.domain.user import UserContext


class ChangeTaskStatusCommand(BaseModel):
    status: TaskStatus


class ChangeTaskStatus:
    def __init__(
        self,
        repository: TaskRepository,
        clock: Clock,
        scheduler: ReminderScheduler,
    ):
        self._repository = repository
        self._clock = clock
        self._scheduler = scheduler

    def execute(self, user: UserContext, task_id: str, command: ChangeTaskStatusCommand) -> Task:
        task = load_owned_task(self._repository, user, task_id)
        task.transition_to(command.status, self._clock.now())
        self._repository.save(task)
        if not task.can_be_modified():
            cancel_reminder(self._scheduler, task.id)
        return task
