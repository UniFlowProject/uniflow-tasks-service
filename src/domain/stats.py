from collections import Counter
from datetime import datetime
from typing import Iterable

from pydantic import BaseModel, Field

from src.domain.enums import TaskStatus
from src.domain.task import Task


class TaskStats(BaseModel):
    total: int = 0
    completed: int = 0
    pending: int = 0
    overdue: int = 0
    by_status: dict[str, int] = Field(default_factory=dict)
    by_priority: dict[str, int] = Field(default_factory=dict)
    by_type: dict[str, int] = Field(default_factory=dict)
    by_subject: dict[str, int] = Field(default_factory=dict)

    @classmethod
    def from_tasks(cls, tasks: Iterable[Task], now: datetime) -> "TaskStats":
        tasks = list(tasks)
        return cls(
            total=len(tasks),
            completed=sum(t.status == TaskStatus.DONE for t in tasks),
            pending=sum(t.can_be_modified() for t in tasks),
            overdue=sum(t.is_overdue(now) for t in tasks),
            by_status=dict(Counter(t.status.value for t in tasks)),
            by_priority=dict(Counter(t.priority.value for t in tasks)),
            by_type=dict(Counter(t.type.value for t in tasks)),
            by_subject=dict(Counter(t.subject_id for t in tasks)),
        )
