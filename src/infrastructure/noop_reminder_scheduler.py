from src.domain.task import Task


class NoopReminderScheduler:
    """Default scheduler when reminders are disabled."""

    def schedule(self, task: Task) -> None:
        pass

    def cancel(self, task_id: str) -> None:
        pass
