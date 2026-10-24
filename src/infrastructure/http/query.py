from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import Field, field_validator

from src.domain.enums import SortOrder, TaskPriority, TaskSortField, TaskStatus
from src.domain.filters import TaskFilter
from src.infrastructure.http.schemas import ApiModel


class TaskListQuery(ApiModel):
    """Query string of GET /tasks; the caller's id is added in to_filter."""

    status: list[TaskStatus] = Field(default_factory=list)
    priority: list[TaskPriority] = Field(default_factory=list)
    subject_id: str | None = None
    period_id: str | None = None
    due_date_from: datetime | None = None
    due_date_to: datetime | None = None
    is_overdue: bool | None = None
    is_due_soon: bool | None = None
    search: str | None = None
    sort_by: TaskSortField = TaskSortField.DUE_DATE
    sort_order: SortOrder = SortOrder.ASC
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=100)
    time_zone: str = "UTC"

    @field_validator("time_zone")
    @classmethod
    def _must_be_iana_name(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError) as error:
            raise ValueError(f"Unknown time zone '{value}'") from error
        return value

    def to_filter(self, user_id: str) -> TaskFilter:
        return TaskFilter(user_id=user_id, **dict(self))
