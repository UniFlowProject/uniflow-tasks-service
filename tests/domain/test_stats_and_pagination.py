from datetime import timedelta

from src.domain.enums import TaskPriority, TaskStatus
from src.domain.pagination import PageInfo
from src.domain.stats import TaskStats


def test_stats_from_tasks(make_task, now):
    tasks = [
        make_task(id="1", status=TaskStatus.DONE, subject_id="a"),
        make_task(id="2", status=TaskStatus.TODO, subject_id="a", due_date=now - timedelta(days=1)),
        make_task(id="3", status=TaskStatus.IN_PROGRESS, subject_id="b", priority=TaskPriority.HIGH),
        make_task(id="4", status=TaskStatus.CANCELLED, subject_id="b"),
    ]

    stats = TaskStats.from_tasks(tasks, now)

    assert stats.total == 4
    assert stats.completed == 1
    assert stats.pending == 2
    assert stats.overdue == 1
    assert stats.by_status["todo"] == 1
    assert stats.by_priority["high"] == 1
    assert stats.by_type["assignment"] == 4
    assert stats.by_subject == {"a": 2, "b": 2}


def test_page_info_middle_page():
    info = PageInfo.of(total=45, page=2, limit=20)
    assert (info.total_pages, info.has_next, info.has_prev) == (3, True, True)


def test_page_info_empty():
    info = PageInfo.of(total=0, page=1, limit=20)
    assert (info.total_pages, info.has_next, info.has_prev) == (0, False, False)
