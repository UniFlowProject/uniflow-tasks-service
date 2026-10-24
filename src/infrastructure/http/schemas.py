from datetime import datetime
from typing import Self

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from src.application.use_cases.change_task_status import ChangeTaskStatusCommand
from src.application.use_cases.create_task import CreateTaskCommand
from src.application.use_cases.list_tasks import TaskPage
from src.application.use_cases.update_task import UpdateTaskCommand
from src.domain.enums import TaskPriority, TaskStatus, TaskType
from src.domain.pagination import PageInfo
from src.domain.stats import TaskStats
from src.domain.task import Task


class ApiModel(BaseModel):
    """Base for every payload: camelCase on the wire, snake_case in Python."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)


class CreateTaskRequest(ApiModel):
    title: str = Field(min_length=1)
    description: str = ""
    subject_id: str = Field(min_length=1)
    period_id: str = Field(min_length=1)
    due_date: datetime
    priority: TaskPriority
    type: TaskType
    estimated_time_hours: int = Field(ge=0)
    tags: list[str] = Field(default_factory=list)
    group_members: list[str] = Field(default_factory=list)
    attachments: list[str] = Field(default_factory=list)

    def to_command(self) -> CreateTaskCommand:
        return CreateTaskCommand(**dict(self))


class UpdateTaskRequest(ApiModel):
    title: str | None = Field(default=None, min_length=1)
    description: str | None = None
    subject_id: str | None = Field(default=None, min_length=1)
    period_id: str | None = Field(default=None, min_length=1)
    due_date: datetime | None = None
    priority: TaskPriority | None = None
    type: TaskType | None = None
    estimated_time_hours: int | None = Field(default=None, ge=0)
    actual_time_hours: int | None = Field(default=None, ge=0)
    tags: list[str] | None = None
    group_members: list[str] | None = None
    attachments: list[str] | None = None

    def to_command(self) -> UpdateTaskCommand:
        # Only fields the client sent: the use case relies on exclude_unset.
        return UpdateTaskCommand(**{name: getattr(self, name) for name in self.model_fields_set})


class ChangeStatusRequest(ApiModel):
    status: TaskStatus

    def to_command(self) -> ChangeTaskStatusCommand:
        return ChangeTaskStatusCommand(status=self.status)


class TaskResponse(ApiModel):
    id: str
    user_id: str
    title: str
    description: str
    subject_id: str
    period_id: str
    due_date: datetime
    status: TaskStatus
    priority: TaskPriority
    type: TaskType
    estimated_time_hours: int
    actual_time_hours: int | None
    tags: list[str]
    group_members: list[str]
    attachments: list[str]
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None

    @classmethod
    def from_task(cls, task: Task) -> Self:
        return cls(**task.model_dump())


class PageInfoResponse(ApiModel):
    total: int
    page: int
    limit: int
    total_pages: int
    has_next: bool
    has_prev: bool

    @classmethod
    def from_page_info(cls, page_info: PageInfo) -> Self:
        return cls(**page_info.model_dump())


class TaskListResponse(ApiModel):
    items: list[TaskResponse]
    page_info: PageInfoResponse

    @classmethod
    def from_page(cls, page: TaskPage) -> Self:
        return cls(
            items=[TaskResponse.from_task(task) for task in page.items],
            page_info=PageInfoResponse.from_page_info(page.page_info),
        )


class TaskStatsResponse(ApiModel):
    total: int
    completed: int
    pending: int
    overdue: int
    by_status: dict[str, int]
    by_priority: dict[str, int]
    by_type: dict[str, int]
    by_subject: dict[str, int]

    @classmethod
    def from_stats(cls, stats: TaskStats) -> Self:
        return cls(**stats.model_dump())


class ErrorDetail(BaseModel):
    field: str
    message: str


class ErrorBody(BaseModel):
    code: str
    message: str
    details: list[ErrorDetail] | None = None


class ErrorResponse(BaseModel):
    error: ErrorBody
