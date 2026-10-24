import json
import re
from datetime import UTC, datetime, timedelta, timezone

import boto3
import pytest
from botocore.exceptions import ClientError
from botocore.stub import Stubber
from moto import mock_aws

from src.infrastructure.eventbridge_reminder_scheduler import EventBridgeReminderScheduler
from tests.application.fakes import FixedClock

GROUP = "reminders"
QUEUE_ARN = "arn:aws:sqs:us-east-1:123456789012:reminders"
ROLE_ARN = "arn:aws:iam::123456789012:role/scheduler"


@pytest.fixture(autouse=True)
def aws_credentials(monkeypatch):
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test")


@pytest.fixture
def client():
    with mock_aws():
        client = boto3.client("scheduler", region_name="us-east-1")
        client.create_schedule_group(Name=GROUP)
        yield client


@pytest.fixture
def scheduler(client, now):
    return EventBridgeReminderScheduler(
        client,
        FixedClock(now),
        group_name=GROUP,
        queue_arn=QUEUE_ARN,
        role_arn=ROLE_ARN,
    )


def _get(client, task_id):
    return client.get_schedule(GroupName=GROUP, Name=f"task-reminder-{task_id}")


def _exists(client, task_id) -> bool:
    try:
        _get(client, task_id)
    except client.exceptions.ResourceNotFoundException:
        return False
    return True


def test_schedule_creates_one_time_schedule_before_due_date(scheduler, client, make_task, now):
    task = make_task(id="t1", due_date=now + timedelta(days=3))

    scheduler.schedule(task)

    schedule = _get(client, "t1")
    assert schedule["Name"] == "task-reminder-t1"
    assert schedule["GroupName"] == GROUP
    assert schedule["ScheduleExpression"] == "at(2026-10-25T12:00:00)"
    assert schedule["ScheduleExpressionTimezone"] == "UTC"
    assert schedule["FlexibleTimeWindow"] == {"Mode": "OFF"}
    assert schedule["ActionAfterCompletion"] == "DELETE"


def test_schedule_targets_the_queue_with_a_minimal_payload(scheduler, client, make_task, now):
    due = now + timedelta(days=3)
    task = make_task(id="t1", user_id="u1", title="Homework", due_date=due)

    scheduler.schedule(task)

    target = _get(client, "t1")["Target"]
    assert target["Arn"] == QUEUE_ARN
    assert target["RoleArn"] == ROLE_ARN
    assert json.loads(target["Input"]) == {
        "taskId": "t1",
        "userId": "u1",
        "title": "Homework",
        "dueDate": due.isoformat(),
    }


def test_fire_time_is_converted_to_utc(client, make_task, now):
    scheduler = EventBridgeReminderScheduler(
        client,
        FixedClock(now),
        group_name=GROUP,
        queue_arn=QUEUE_ARN,
        role_arn=ROLE_ARN,
        lead_time=timedelta(hours=2),
    )
    local = datetime(2026, 10, 30, 10, 30, 15, 999, tzinfo=UTC).astimezone(
        timezone(timedelta(hours=-5))
    )

    scheduler.schedule(make_task(due_date=local))

    assert _get(client, "t1")["ScheduleExpression"] == "at(2026-10-30T08:30:15)"


def test_task_ids_yield_valid_schedule_names(scheduler, client, make_task, now):
    task_id = "3f2b8c1e-9a4d-4e6b-8c7a-1d2e3f4a5b6c"

    scheduler.schedule(make_task(id=task_id))

    name = _get(client, task_id)["Name"]
    assert len(name) <= 64
    assert re.fullmatch(r"[0-9a-zA-Z\-_.]+", name)


def test_schedule_replaces_previous_reminder(scheduler, client, make_task, now):
    scheduler.schedule(make_task(due_date=now + timedelta(days=3), title="Old"))

    scheduler.schedule(make_task(due_date=now + timedelta(days=5), title="New"))

    schedule = _get(client, "t1")
    assert schedule["ScheduleExpression"] == "at(2026-10-27T12:00:00)"
    assert json.loads(schedule["Target"]["Input"])["title"] == "New"


@pytest.mark.parametrize("hours_until_due", [24, 10, 0, -5])
def test_schedule_skips_when_fire_time_is_not_in_the_future(
    scheduler, client, make_task, now, hours_until_due
):
    scheduler.schedule(make_task(due_date=now + timedelta(hours=hours_until_due)))

    assert not _exists(client, "t1")


def test_schedule_removes_stale_reminder_when_fire_time_is_not_in_the_future(
    scheduler, client, make_task, now
):
    scheduler.schedule(make_task(due_date=now + timedelta(days=3)))

    scheduler.schedule(make_task(due_date=now + timedelta(hours=3)))

    assert not _exists(client, "t1")


def test_cancel_deletes_the_schedule(scheduler, client, make_task, now):
    scheduler.schedule(make_task(due_date=now + timedelta(days=3)))

    scheduler.cancel("t1")

    assert not _exists(client, "t1")


def test_cancel_missing_schedule_is_a_noop(scheduler):
    scheduler.cancel("missing")


def test_other_client_errors_propagate_on_schedule(make_task, now):
    client = boto3.client("scheduler", region_name="us-east-1")
    scheduler = EventBridgeReminderScheduler(
        client, FixedClock(now), group_name=GROUP, queue_arn=QUEUE_ARN, role_arn=ROLE_ARN
    )
    with Stubber(client) as stubber:
        stubber.add_client_error("create_schedule", "AccessDeniedException")

        with pytest.raises(ClientError):
            scheduler.schedule(make_task(due_date=now + timedelta(days=3)))


def test_other_client_errors_propagate_on_cancel(now):
    client = boto3.client("scheduler", region_name="us-east-1")
    scheduler = EventBridgeReminderScheduler(
        client, FixedClock(now), group_name=GROUP, queue_arn=QUEUE_ARN, role_arn=ROLE_ARN
    )
    with Stubber(client) as stubber:
        stubber.add_client_error("delete_schedule", "InternalServerException")

        with pytest.raises(ClientError):
            scheduler.cancel("t1")
