from datetime import UTC

from boto3.dynamodb.conditions import Key

from src.application.ports.clock import Clock
from src.domain.filters import TaskFilter
from src.domain.pagination import PageInfo
from src.domain.task import Task
from src.infrastructure.dynamo_table import GSI_HASH_KEY, GSI_NAME, GSI_RANGE_KEY
from src.infrastructure.task_query import select_page

_TASK_ID = "task_id"


class DynamoTaskRepository:
    """DynamoDB adapter.

    Listings read the user's items from the `user-period-index` GSI (projecting
    ALL attributes, so a Task is rebuilt without a second read) and apply the
    remaining filters, sorting and pagination in memory: a user has at most a
    few hundred tasks.
    """

    def __init__(self, table, clock: Clock, query_page_size: int | None = None):
        self._table = table
        self._clock = clock
        self._query_page_size = query_page_size

    def get(self, task_id: str) -> Task | None:
        item = self._table.get_item(Key={_TASK_ID: task_id}).get("Item")
        return _from_item(item) if item else None

    def list(self, task_filter: TaskFilter) -> tuple[list[Task], PageInfo]:
        condition = Key(GSI_HASH_KEY).eq(task_filter.user_id)
        if task_filter.period_id is not None:
            condition &= Key(GSI_RANGE_KEY).begins_with(f"{task_filter.period_id}#")
        return select_page(self._query(condition), task_filter, self._clock.now())

    def list_all(self, user_id: str) -> list[Task]:
        return list(self._query(Key(GSI_HASH_KEY).eq(user_id)))

    def save(self, task: Task) -> None:
        self._table.put_item(Item=_to_item(task))

    def delete(self, task_id: str) -> None:
        self._table.delete_item(Key={_TASK_ID: task_id})

    def _query(self, condition) -> list[Task]:
        params = {"IndexName": GSI_NAME, "KeyConditionExpression": condition}
        if self._query_page_size is not None:
            params["Limit"] = self._query_page_size
        tasks: list[Task] = []
        while True:
            response = self._table.query(**params)
            tasks.extend(_from_item(item) for item in response["Items"])
            last_key = response.get("LastEvaluatedKey")
            if last_key is None:
                return tasks
            params["ExclusiveStartKey"] = last_key


def _to_item(task: Task) -> dict:
    item = task.model_dump(mode="json")
    item[_TASK_ID] = item.pop("id")
    due = task.due_date.astimezone(UTC).isoformat(timespec="seconds")
    item[GSI_RANGE_KEY] = f"{task.period_id}#{due}#{task.id}"
    return item


def _from_item(item: dict) -> Task:
    data = {k: v for k, v in item.items() if k != GSI_RANGE_KEY}
    data["id"] = data.pop(_TASK_ID)
    return Task.model_validate(data)
