import json
from datetime import UTC, timedelta

from botocore.exceptions import ClientError

from src.application.ports.clock import Clock
from src.domain.task import Task

_NAME_PREFIX = "task-reminder-"


class EventBridgeReminderScheduler:
    """EventBridge Scheduler adapter.

    Each reminder is a one-time schedule that delivers a small JSON payload to
    an SQS queue and deletes itself once it has fired.
    """

    def __init__(
        self,
        client,
        clock: Clock,
        group_name: str,
        queue_arn: str,
        role_arn: str,
        lead_time: timedelta = timedelta(hours=24),
    ):
        self._client = client
        self._clock = clock
        self._group_name = group_name
        self._queue_arn = queue_arn
        self._role_arn = role_arn
        self._lead_time = lead_time

    def schedule(self, task: Task) -> None:
        fire_at = (task.due_date - self._lead_time).astimezone(UTC)
        if fire_at <= self._clock.now():
            self.cancel(task.id)
            return
        params = {
            "Name": _schedule_name(task.id),
            "GroupName": self._group_name,
            "ScheduleExpression": f"at({fire_at:%Y-%m-%dT%H:%M:%S})",
            "ScheduleExpressionTimezone": "UTC",
            "FlexibleTimeWindow": {"Mode": "OFF"},
            "Target": {
                "Arn": self._queue_arn,
                "RoleArn": self._role_arn,
                "Input": _payload(task),
            },
        }
        try:
            self._client.create_schedule(**params, ActionAfterCompletion="DELETE")
        except self._client.exceptions.ConflictException:
            self._client.update_schedule(**params, ActionAfterCompletion="DELETE")

    def cancel(self, task_id: str) -> None:
        try:
            self._client.delete_schedule(
                Name=_schedule_name(task_id), GroupName=self._group_name
            )
        except self._client.exceptions.ResourceNotFoundException:
            pass


def _schedule_name(task_id: str) -> str:
    return f"{_NAME_PREFIX}{task_id}"


def _payload(task: Task) -> str:
    return json.dumps(
        {
            "taskId": task.id,
            "userId": task.user_id,
            "title": task.title,
            "dueDate": task.due_date.isoformat(),
        }
    )
