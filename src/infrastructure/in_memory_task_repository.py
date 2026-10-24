from collections.abc import Callable
from datetime import datetime

from src.application.ports.clock import Clock
from src.domain.enums import SortOrder, TaskPriority, TaskSortField, TaskStatus
from src.domain.filters import TaskFilter
from src.domain.pagination import PageInfo
from src.domain.task import Task

_PRIORITY_RANK = {p: rank for rank, p in enumerate(TaskPriority)}
_STATUS_RANK = {s: rank for rank, s in enumerate(TaskStatus)}

_SORT_KEYS: dict[TaskSortField, Callable[[Task], object]] = {
    TaskSortField.DUE_DATE: lambda t: t.due_date,
    TaskSortField.PRIORITY: lambda t: _PRIORITY_RANK[t.priority],
    TaskSortField.STATUS: lambda t: _STATUS_RANK[t.status],
    TaskSortField.CREATED_AT: lambda t: t.created_at,
}


class InMemoryTaskRepository:
    """Temporary stand-in until the DynamoDB adapter exists.

    Filtering ignores `time_zone`: all comparisons are on aware datetimes.
    """

    def __init__(self, clock: Clock):
        self._clock = clock
        self._tasks: dict[str, Task] = {}

    def get(self, task_id: str) -> Task | None:
        return self._tasks.get(task_id)

    def list(self, task_filter: TaskFilter) -> tuple[list[Task], PageInfo]:
        now = self._clock.now()
        matching = [
            t for t in self._tasks.values() if self._matches(t, task_filter, now)
        ]
        matching.sort(
            key=_SORT_KEYS[task_filter.sort_by],
            reverse=task_filter.sort_order == SortOrder.DESC,
        )
        start = (task_filter.page - 1) * task_filter.limit
        page_items = matching[start : start + task_filter.limit]
        return page_items, PageInfo.of(len(matching), task_filter.page, task_filter.limit)

    def list_all(self, user_id: str) -> list[Task]:
        return [t for t in self._tasks.values() if t.user_id == user_id]

    def save(self, task: Task) -> None:
        self._tasks[task.id] = task

    def delete(self, task_id: str) -> None:
        self._tasks.pop(task_id, None)

    @staticmethod
    def _matches(task: Task, task_filter: TaskFilter, now: datetime) -> bool:
        # An empty status/priority list means "no filter". Checks run lazily, cheapest first.
        if task.user_id != task_filter.user_id:
            return False
        if task_filter.status and task.status not in task_filter.status:
            return False
        if task_filter.priority and task.priority not in task_filter.priority:
            return False
        if task_filter.subject_id is not None and task.subject_id != task_filter.subject_id:
            return False
        if task_filter.period_id is not None and task.period_id != task_filter.period_id:
            return False
        if task_filter.due_date_from is not None and task.due_date < task_filter.due_date_from:
            return False
        if task_filter.due_date_to is not None and task.due_date > task_filter.due_date_to:
            return False
        if task_filter.is_overdue is not None and task.is_overdue(now) != task_filter.is_overdue:
            return False
        if task_filter.is_due_soon is not None and task.is_due_soon(now) != task_filter.is_due_soon:
            return False
        if task_filter.search is not None:
            haystack = f"{task.title} {task.description}".lower()
            return task_filter.search.lower() in haystack
        return True
