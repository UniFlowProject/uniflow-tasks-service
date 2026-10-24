from datetime import datetime

from src.domain.filters import TaskFilter
from src.domain.pagination import PageInfo
from src.domain.task import Task


class InMemoryTaskRepository:
    def __init__(self, *tasks: Task):
        self.tasks = {t.id: t for t in tasks}

    def get(self, task_id: str) -> Task | None:
        return self.tasks.get(task_id)

    def list(self, task_filter: TaskFilter) -> tuple[list[Task], PageInfo]:
        mine = [t for t in self.tasks.values() if t.user_id == task_filter.user_id]
        start = (task_filter.page - 1) * task_filter.limit
        page = mine[start : start + task_filter.limit]
        return page, PageInfo.of(len(mine), task_filter.page, task_filter.limit)

    def list_all(self, user_id: str) -> list[Task]:
        return [t for t in self.tasks.values() if t.user_id == user_id]

    def save(self, task: Task) -> None:
        self.tasks[task.id] = task

    def delete(self, task_id: str) -> None:
        self.tasks.pop(task_id, None)


class FixedClock:
    def __init__(self, now: datetime):
        self._now = now

    def now(self) -> datetime:
        return self._now


class SequentialIds:
    def __init__(self):
        self._n = 0

    def new_id(self) -> str:
        self._n += 1
        return f"id-{self._n}"


class RecordingScheduler:
    def __init__(self, fail: bool = False):
        self.scheduled: list[Task] = []
        self.cancelled: list[str] = []
        self.fail = fail

    def schedule(self, task: Task) -> None:
        if self.fail:
            raise RuntimeError("scheduler down")
        self.scheduled.append(task)

    def cancel(self, task_id: str) -> None:
        if self.fail:
            raise RuntimeError("scheduler down")
        self.cancelled.append(task_id)
