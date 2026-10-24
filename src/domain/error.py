from src.domain.enums import TaskStatus


class DomainError(Exception):
    """Base class for every error raised by business rules."""


class TaskNotFoundError(DomainError):
    def __init__(self, task_id: str):
        super().__init__(f"Task '{task_id}' not found")
        self.task_id = task_id


class ForbiddenError(DomainError):
    def __init__(self, task_id: str):
        super().__init__(f"Not allowed to access task '{task_id}'")
        self.task_id = task_id


class TaskNotModifiableError(DomainError):
    def __init__(self, task_id: str, status: TaskStatus):
        super().__init__(f"Task '{task_id}' is {status} and cannot be modified")
        self.task_id = task_id
        self.status = status


class InvalidStatusTransitionError(DomainError):
    def __init__(self, current: TaskStatus, target: TaskStatus):
        super().__init__(f"Cannot move task from '{current}' to '{target}'")
        self.current = current
        self.target = target
