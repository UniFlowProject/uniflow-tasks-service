from enum import StrEnum
from typing import Self

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings


class RepositoryKind(StrEnum):
    MEMORY = "memory"
    DYNAMODB = "dynamodb"


class ReminderSchedulerKind(StrEnum):
    NOOP = "noop"
    EVENTBRIDGE = "eventbridge"


class Settings(BaseSettings):
    """Read from environment variables named after the fields (case-insensitive)."""

    tasks_repository: RepositoryKind = RepositoryKind.MEMORY
    tasks_table_name: str = "uniflow-tasks"
    aws_region: str = "us-east-1"
    dynamodb_endpoint_url: str | None = None
    reminder_scheduler: ReminderSchedulerKind = ReminderSchedulerKind.NOOP
    reminder_group_name: str = "default"
    reminder_queue_arn: str | None = None
    reminder_role_arn: str | None = None
    reminder_lead_time_hours: int = Field(default=24, ge=0)

    @model_validator(mode="after")
    def _eventbridge_requires_arns(self) -> Self:
        if self.reminder_scheduler == ReminderSchedulerKind.EVENTBRIDGE and not (
            self.reminder_queue_arn and self.reminder_role_arn
        ):
            raise ValueError(
                "REMINDER_QUEUE_ARN and REMINDER_ROLE_ARN are required "
                "when REMINDER_SCHEDULER=eventbridge"
            )
        return self
