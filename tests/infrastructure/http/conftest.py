import pytest
from fastapi.testclient import TestClient

from src.infrastructure.http.app import create_app
from src.infrastructure.http.container import Container
from src.infrastructure.http.headers import USER_ID_HEADER
from tests.application.fakes import FixedClock, RecordingScheduler, SequentialIds


@pytest.fixture
def scheduler() -> RecordingScheduler:
    return RecordingScheduler()


@pytest.fixture
def app(now, repo, scheduler):
    container = Container(
        repository=repo,
        clock=FixedClock(now),
        ids=SequentialIds(),
        scheduler=scheduler,
    )
    return create_app(container)


@pytest.fixture
def auth() -> dict[str, str]:
    return {USER_ID_HEADER: "u1"}


@pytest.fixture
def client(app, auth) -> TestClient:
    return TestClient(app, headers=auth, raise_server_exceptions=False)


@pytest.fixture
def anonymous_client(app) -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def new_task_body() -> dict:
    return {
        "title": "Essay",
        "subjectId": "s1",
        "periodId": "p1",
        "dueDate": "2026-11-01T10:00:00Z",
        "priority": "high",
        "type": "essay",
        "estimatedTimeHours": 4,
    }
