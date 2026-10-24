import pytest

from src.infrastructure.in_memory_task_repository import InMemoryTaskRepository
from tests.application.fakes import FixedClock


@pytest.fixture
def repo(now) -> InMemoryTaskRepository:
    return InMemoryTaskRepository(FixedClock(now))
