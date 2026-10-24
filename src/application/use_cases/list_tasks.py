from pydantic import BaseModel

from src.application.ports.task_repository import TaskRepository
from src.domain.filters import TaskFilter
from src.domain.pagination import PageInfo
from src.domain.task import Task


class TaskPage(BaseModel):
    items: list[Task]
    page_info: PageInfo


class ListTasks:
    def __init__(self, repository: TaskRepository):
        self._repository = repository

    def execute(self, task_filter: TaskFilter) -> TaskPage:
        items, page_info = self._repository.list(task_filter)
        return TaskPage(items=items, page_info=page_info)
