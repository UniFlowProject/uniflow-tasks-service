from typing import Protocol

from src.domain.filters import TaskFilter
from src.domain.pagination import PageInfo
from src.domain.task import Task


class TaskRepository(Protocol):
    def get(self, task_id: str) -> Task | None: ...

    def list(self, task_filter: TaskFilter) -> tuple[list[Task], PageInfo]: ...

    def list_all(self, user_id: str) -> list[Task]:
        """Every task of the user, unpaginated. Used to compute stats."""
        ...

    def save(self, task: Task) -> None: ...

    def delete(self, task_id: str) -> None: ...
