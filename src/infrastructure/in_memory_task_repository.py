from src.application.ports.clock import Clock
from src.domain.filters import TaskFilter
from src.domain.pagination import PageInfo
from src.domain.task import Task
from src.infrastructure.task_query import select_page


class InMemoryTaskRepository:
    """Temporary stand-in used when no DynamoDB table is configured.

    Filtering ignores `time_zone`: all comparisons are on aware datetimes.
    """

    def __init__(self, clock: Clock):
        self._clock = clock
        self._tasks: dict[str, Task] = {}

    def get(self, task_id: str) -> Task | None:
        return self._tasks.get(task_id)

    def list(self, task_filter: TaskFilter) -> tuple[list[Task], PageInfo]:
        return select_page(self._tasks.values(), task_filter, self._clock.now())

    def list_all(self, user_id: str) -> list[Task]:
        return [t for t in self._tasks.values() if t.user_id == user_id]

    def save(self, task: Task) -> None:
        self._tasks[task.id] = task

    def delete(self, task_id: str) -> None:
        self._tasks.pop(task_id, None)
