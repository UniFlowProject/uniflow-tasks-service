from enum import StrEnum

from pydantic_settings import BaseSettings


class RepositoryKind(StrEnum):
    MEMORY = "memory"
    DYNAMODB = "dynamodb"


class Settings(BaseSettings):
    """Read from environment variables named after the fields (case-insensitive)."""

    tasks_repository: RepositoryKind = RepositoryKind.MEMORY
    tasks_table_name: str = "uniflow-tasks"
    aws_region: str = "us-east-1"
    dynamodb_endpoint_url: str | None = None
