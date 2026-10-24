from dataclasses import dataclass
from datetime import timedelta

import boto3

from src.application.ports.clock import Clock
from src.application.ports.id_generator import IdGenerator
from src.application.ports.reminder_scheduler import ReminderScheduler
from src.application.ports.task_repository import TaskRepository
from src.infrastructure.dynamo_task_repository import DynamoTaskRepository
from src.infrastructure.eventbridge_reminder_scheduler import EventBridgeReminderScheduler
from src.infrastructure.in_memory_task_repository import InMemoryTaskRepository
from src.infrastructure.noop_reminder_scheduler import NoopReminderScheduler
from src.infrastructure.settings import ReminderSchedulerKind, RepositoryKind, Settings
from src.infrastructure.system_clock import SystemClock
from src.infrastructure.uuid_generator import UuidGenerator


@dataclass(frozen=True)
class Container:
    """Adapters shared by every request of one application instance."""

    repository: TaskRepository
    clock: Clock
    ids: IdGenerator
    scheduler: ReminderScheduler


def build_default_container(settings: Settings | None = None) -> Container:
    settings = settings or Settings()
    clock = SystemClock()
    return Container(
        repository=_build_repository(settings, clock),
        clock=clock,
        ids=UuidGenerator(),
        scheduler=_build_scheduler(settings, clock),
    )


def _build_repository(settings: Settings, clock: Clock) -> TaskRepository:
    if settings.tasks_repository == RepositoryKind.DYNAMODB:
        dynamodb = boto3.resource(
            "dynamodb",
            region_name=settings.aws_region,
            endpoint_url=settings.dynamodb_endpoint_url,
        )
        return DynamoTaskRepository(dynamodb.Table(settings.tasks_table_name), clock)
    return InMemoryTaskRepository(clock)


def _build_scheduler(settings: Settings, clock: Clock) -> ReminderScheduler:
    if settings.reminder_scheduler == ReminderSchedulerKind.EVENTBRIDGE:
        return EventBridgeReminderScheduler(
            boto3.client("scheduler", region_name=settings.aws_region),
            clock,
            group_name=settings.reminder_group_name,
            queue_arn=settings.reminder_queue_arn,
            role_arn=settings.reminder_role_arn,
            lead_time=timedelta(hours=settings.reminder_lead_time_hours),
        )
    return NoopReminderScheduler()
