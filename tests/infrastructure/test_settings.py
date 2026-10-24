import pytest
from pydantic import ValidationError

from src.infrastructure.settings import ReminderSchedulerKind, RepositoryKind, Settings


def test_defaults_to_memory_repository(monkeypatch):
    monkeypatch.delenv("TASKS_REPOSITORY", raising=False)

    settings = Settings()

    assert settings.tasks_repository == RepositoryKind.MEMORY
    assert settings.dynamodb_endpoint_url is None


def test_reads_environment(monkeypatch):
    monkeypatch.setenv("TASKS_REPOSITORY", "dynamodb")
    monkeypatch.setenv("TASKS_TABLE_NAME", "my-tasks")
    monkeypatch.setenv("AWS_REGION", "eu-west-1")
    monkeypatch.setenv("DYNAMODB_ENDPOINT_URL", "http://localhost:8000")

    settings = Settings()

    assert settings.tasks_repository == RepositoryKind.DYNAMODB
    assert settings.tasks_table_name == "my-tasks"
    assert settings.aws_region == "eu-west-1"
    assert settings.dynamodb_endpoint_url == "http://localhost:8000"


def test_reminder_defaults(monkeypatch):
    for name in ("REMINDER_SCHEDULER", "REMINDER_GROUP_NAME", "REMINDER_QUEUE_ARN",
                 "REMINDER_ROLE_ARN", "REMINDER_LEAD_TIME_HOURS"):
        monkeypatch.delenv(name, raising=False)

    settings = Settings()

    assert settings.reminder_scheduler == ReminderSchedulerKind.NOOP
    assert settings.reminder_group_name == "default"
    assert settings.reminder_queue_arn is None
    assert settings.reminder_role_arn is None
    assert settings.reminder_lead_time_hours == 24


def test_reads_reminder_environment(monkeypatch):
    monkeypatch.setenv("REMINDER_SCHEDULER", "eventbridge")
    monkeypatch.setenv("REMINDER_GROUP_NAME", "uniflow")
    monkeypatch.setenv("REMINDER_QUEUE_ARN", "arn:queue")
    monkeypatch.setenv("REMINDER_ROLE_ARN", "arn:role")
    monkeypatch.setenv("REMINDER_LEAD_TIME_HOURS", "12")

    settings = Settings()

    assert settings.reminder_scheduler == ReminderSchedulerKind.EVENTBRIDGE
    assert settings.reminder_group_name == "uniflow"
    assert settings.reminder_queue_arn == "arn:queue"
    assert settings.reminder_role_arn == "arn:role"
    assert settings.reminder_lead_time_hours == 12


@pytest.mark.parametrize(
    "arns", [{}, {"reminder_queue_arn": "arn:queue"}, {"reminder_role_arn": "arn:role"}]
)
def test_eventbridge_scheduler_requires_queue_and_role_arns(monkeypatch, arns):
    monkeypatch.delenv("REMINDER_QUEUE_ARN", raising=False)
    monkeypatch.delenv("REMINDER_ROLE_ARN", raising=False)

    with pytest.raises(ValidationError):
        Settings(reminder_scheduler=ReminderSchedulerKind.EVENTBRIDGE, **arns)


def test_noop_scheduler_does_not_require_arns(monkeypatch):
    monkeypatch.delenv("REMINDER_QUEUE_ARN", raising=False)

    Settings(reminder_scheduler=ReminderSchedulerKind.NOOP)
