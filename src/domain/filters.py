from datetime import datetime

from pydantic import BaseModel, Field

from src.domain.enums import SortOrder, TaskPriority, TaskSortField, TaskStatus


class TaskFilter(BaseModel):
    user_id: str
    status: list[TaskStatus] = Field(default_factory=list)
    priority: list[TaskPriority] = Field(default_factory=list)
    subject_id: str | None = None
    period_id: str | None = None
    due_date_from: datetime | None = None
    due_date_to: datetime | None = None
    is_overdue: bool | None = None
    is_due_soon: bool | None = None  # due within the next 24h
    search: str | None = None
    sort_by: TaskSortField = TaskSortField.DUE_DATE
    sort_order: SortOrder = SortOrder.ASC
    page: int = Field(default=1, ge=1)
    limit: int = Field(default=20, ge=1, le=100)
    time_zone: str = "UTC"  # IANA name, e.g. America/Costa_Rica
