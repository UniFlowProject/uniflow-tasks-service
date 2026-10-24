from src.application.ports.task_repository import TaskRepository
from src.domain.error import TaskNotFoundError
from src.domain.task import Task
from src.domain.user import UserContext


def load_owned_task(repository: TaskRepository, user: UserContext, task_id: str) -> Task:
    task = repository.get(task_id)
    if task is None:
        raise TaskNotFoundError(task_id)
    task.ensure_owned_by(user.id)
    return task
