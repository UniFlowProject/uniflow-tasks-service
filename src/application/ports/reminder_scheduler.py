from typing import Protocol

from src.domain.task import Task


class ReminderScheduler(Protocol):
    """Schedules a one-time reminder before a task is due.

    Lead time is an adapter concern. Both calls must be idempotent:
    scheduling again replaces the previous reminder, cancelling a missing
    one is a no-op.
    """

    def schedule(self, task: Task) -> None: ...

    def cancel(self, task_id: str) -> None: ...
