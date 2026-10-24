from datetime import datetime, timedelta
from typing import Self

from pydantic import BaseModel, Field, model_validator

from src.domain.enums import TaskPriority, TaskStatus, TaskType
from src.domain.error import (
    ForbiddenError,
    InvalidStatusTransitionError,
    TaskNotModifiableError,
)

ALLOWED_TRANSITIONS: dict[TaskStatus, frozenset[TaskStatus]] = {
    TaskStatus.TODO: frozenset({TaskStatus.IN_PROGRESS, TaskStatus.CANCELLED}),
    TaskStatus.IN_PROGRESS: frozenset(
        {TaskStatus.TODO, TaskStatus.IN_REVIEW, TaskStatus.DONE, TaskStatus.CANCELLED}
    ),
    TaskStatus.IN_REVIEW: frozenset(
        {TaskStatus.IN_PROGRESS, TaskStatus.DONE, TaskStatus.CANCELLED}
    ),
    TaskStatus.DONE: frozenset(),
    TaskStatus.CANCELLED: frozenset(),
}

DUE_SOON_WINDOW = timedelta(hours=24)


class Task(BaseModel):
    id: str
    user_id: str
    title: str
    description: str = ""
    subject_id: str
    period_id: str
    due_date: datetime
    status: TaskStatus
    priority: TaskPriority
    type: TaskType
    estimated_time_hours: int = Field(ge=0)
    actual_time_hours: int | None = Field(default=None, ge=0)
    tags: list[str] = Field(default_factory=list)
    group_members: list[str] = Field(default_factory=list)
    attachments: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None = None

    @model_validator(mode="after")
    def _group_members_only_in_group_work(self) -> Self:
        if self.group_members and not self.is_group_work:
            raise ValueError("group_members requires type 'group-work'")
        return self

    @property
    def is_group_work(self) -> bool:
        return self.type == TaskType.GROUP_WORK

    def is_completed(self) -> bool:
        return self.status == TaskStatus.DONE

    def is_cancelled(self) -> bool:
        return self.status == TaskStatus.CANCELLED

    def can_be_modified(self) -> bool:
        return self.status not in (TaskStatus.DONE, TaskStatus.CANCELLED)

    def can_be_deleted(self) -> bool:
        return self.can_be_modified()

    def is_overdue(self, now: datetime) -> bool:
        return self.can_be_modified() and self.due_date < now

    def is_due_soon(self, now: datetime) -> bool:
        return self.can_be_modified() and now <= self.due_date <= now + DUE_SOON_WINDOW

    def ensure_modifiable(self) -> None:
        if not self.can_be_modified():
            raise TaskNotModifiableError(self.id, self.status)

    def ensure_owned_by(self, user_id: str) -> None:
        if self.user_id != user_id:
            raise ForbiddenError(self.id)

    def transition_to(self, new_status: TaskStatus, now: datetime) -> None:
        if new_status not in ALLOWED_TRANSITIONS[self.status]:
            raise InvalidStatusTransitionError(self.status, new_status)
        self.status = new_status
        self.updated_at = now
        if new_status == TaskStatus.DONE:
            self.completed_at = now
