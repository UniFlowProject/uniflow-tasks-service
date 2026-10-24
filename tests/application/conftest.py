import pytest

from src.domain.user import UserContext
from tests.application.fakes import (
    FixedClock,
    InMemoryTaskRepository,
    RecordingScheduler,
    SequentialIds,
)


@pytest.fixture
def user() -> UserContext:
    return UserContext(id="u1")


@pytest.fixture
def other_user() -> UserContext:
    return UserContext(id="u2")


@pytest.fixture
def clock(now) -> FixedClock:
    return FixedClock(now)


@pytest.fixture
def scheduler() -> RecordingScheduler:
    return RecordingScheduler()


@pytest.fixture
def ids() -> SequentialIds:
    return SequentialIds()


@pytest.fixture
def repo(make_task) -> InMemoryTaskRepository:
    return InMemoryTaskRepository(make_task())
