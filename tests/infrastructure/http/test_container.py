import boto3
from moto import mock_aws

from src.infrastructure.dynamo_table import create_tasks_table
from src.infrastructure.dynamo_task_repository import DynamoTaskRepository
from src.infrastructure.eventbridge_reminder_scheduler import EventBridgeReminderScheduler
from src.infrastructure.http.container import build_default_container
from src.infrastructure.in_memory_task_repository import InMemoryTaskRepository
from src.infrastructure.noop_reminder_scheduler import NoopReminderScheduler
from src.infrastructure.settings import ReminderSchedulerKind, RepositoryKind, Settings


def test_builds_in_memory_repository_by_default():
    container = build_default_container(Settings(tasks_repository=RepositoryKind.MEMORY))

    assert isinstance(container.repository, InMemoryTaskRepository)


def test_builds_dynamodb_repository_when_configured(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test")
    settings = Settings(
        tasks_repository=RepositoryKind.DYNAMODB,
        tasks_table_name="tasks",
        aws_region="us-east-1",
    )
    with mock_aws():
        create_tasks_table(boto3.resource("dynamodb", region_name="us-east-1"), "tasks")

        container = build_default_container(settings)

        assert isinstance(container.repository, DynamoTaskRepository)
        assert container.repository.list_all("u1") == []


def test_builds_noop_scheduler_by_default():
    container = build_default_container(Settings())

    assert isinstance(container.scheduler, NoopReminderScheduler)


def test_builds_eventbridge_scheduler_when_configured(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test")
    settings = Settings(
        reminder_scheduler=ReminderSchedulerKind.EVENTBRIDGE,
        reminder_queue_arn="arn:aws:sqs:us-east-1:123456789012:reminders",
        reminder_role_arn="arn:aws:iam::123456789012:role/scheduler",
    )

    container = build_default_container(settings)

    assert isinstance(container.scheduler, EventBridgeReminderScheduler)
