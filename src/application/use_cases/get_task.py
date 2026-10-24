from src.application.ports.task_repository import TaskRepository
from src.application.use_cases.loader import load_owned_task
from src.domain.task import Task
from src.domain.user import UserContext


class GetTask:
    def __init__(self, repository: TaskRepository):
        self._repository = repository

    def execute(self, user: UserContext, task_id: str) -> Task:
        return load_owned_task(self._repository, user, task_id)
