from src.application.ports.clock import Clock
from src.application.ports.task_repository import TaskRepository
from src.domain.stats import TaskStats
from src.domain.user import UserContext


class GetTaskStats:
    def __init__(self, repository: TaskRepository, clock: Clock):
        self._repository = repository
        self._clock = clock

    def execute(self, user: UserContext) -> TaskStats:
        return TaskStats.from_tasks(self._repository.list_all(user.id), self._clock.now())
