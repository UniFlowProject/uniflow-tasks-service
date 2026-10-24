from src.application.ports.reminder_scheduler import ReminderScheduler
from src.application.ports.task_repository import TaskRepository
from src.application.reminders import cancel_reminder
from src.application.use_cases.loader import load_owned_task
from src.domain.error import TaskNotModifiableError
from src.domain.user import UserContext


class DeleteTask:
    def __init__(self, repository: TaskRepository, scheduler: ReminderScheduler):
        self._repository = repository
        self._scheduler = scheduler

    def execute(self, user: UserContext, task_id: str) -> None:
        task = load_owned_task(self._repository, user, task_id)
        if not task.can_be_deleted():
            raise TaskNotModifiableError(task.id, task.status)
        self._repository.delete(task.id)
        cancel_reminder(self._scheduler, task.id)
