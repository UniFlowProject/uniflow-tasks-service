from src.domain.task import Task


class NoopReminderScheduler:
    """Temporary stand-in until the EventBridge adapter exists."""

    def schedule(self, task: Task) -> None:
        pass

    def cancel(self, task_id: str) -> None:
        pass
