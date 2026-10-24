from dataclasses import dataclass

from src.application.ports.clock import Clock
from src.application.ports.id_generator import IdGenerator
from src.application.ports.reminder_scheduler import ReminderScheduler
from src.application.ports.task_repository import TaskRepository
from src.infrastructure.in_memory_task_repository import InMemoryTaskRepository
from src.infrastructure.noop_reminder_scheduler import NoopReminderScheduler
from src.infrastructure.system_clock import SystemClock
from src.infrastructure.uuid_generator import UuidGenerator


@dataclass(frozen=True)
class Container:
    """Adapters shared by every request of one application instance."""

    repository: TaskRepository
    clock: Clock
    ids: IdGenerator
    scheduler: ReminderScheduler


def build_default_container() -> Container:
    clock = SystemClock()
    return Container(
        repository=InMemoryTaskRepository(clock),
        clock=clock,
        ids=UuidGenerator(),
        scheduler=NoopReminderScheduler(),
    )
