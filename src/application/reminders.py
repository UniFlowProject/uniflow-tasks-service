import logging

from src.application.ports.reminder_scheduler import ReminderScheduler
from src.domain.task import Task

logger = logging.getLogger(__name__)


def schedule_reminder(scheduler: ReminderScheduler, task: Task) -> None:
    """Best effort: a scheduler outage must never fail the task operation."""
    try:
        scheduler.schedule(task)
    except Exception:
        logger.warning("Could not schedule reminder for task %s", task.id, exc_info=True)


def cancel_reminder(scheduler: ReminderScheduler, task_id: str) -> None:
    try:
        scheduler.cancel(task_id)
    except Exception:
        logger.warning("Could not cancel reminder for task %s", task_id, exc_info=True)
