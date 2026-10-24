from datetime import UTC, datetime, timedelta
from uuid import UUID

from src.infrastructure.system_clock import SystemClock
from src.infrastructure.uuid_generator import UuidGenerator


def test_system_clock_returns_timezone_aware_utc_now():
    before = datetime.now(UTC)
    now = SystemClock().now()
    after = datetime.now(UTC)

    assert now.tzinfo is not None
    assert now.utcoffset() == timedelta(0)
    assert before <= now <= after


def test_uuid_generator_returns_valid_uuid_strings():
    task_id = UuidGenerator().new_id()

    assert str(UUID(task_id)) == task_id


def test_uuid_generator_returns_unique_ids():
    generator = UuidGenerator()

    assert generator.new_id() != generator.new_id()
