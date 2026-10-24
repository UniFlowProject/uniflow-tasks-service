from src.infrastructure.noop_reminder_scheduler import NoopReminderScheduler


def test_schedule_and_cancel_do_nothing_and_never_fail(make_task):
    scheduler = NoopReminderScheduler()

    assert scheduler.schedule(make_task()) is None
    assert scheduler.cancel("t1") is None
    assert scheduler.cancel("unknown") is None
