from enum import StrEnum


class TaskStatus(StrEnum):
    TODO = "todo"
    IN_PROGRESS = "in-progress"
    IN_REVIEW = "in-review"
    DONE = "done"
    CANCELLED = "cancelled"


class TaskPriority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskType(StrEnum):
    ASSIGNMENT = "assignment"
    EXAM = "exam"
    READING = "reading"
    PRESENTATION = "presentation"
    LAB = "lab"
    QUIZ = "quiz"
    ESSAY = "essay"
    GROUP_WORK = "group-work"


class SortOrder(StrEnum):
    ASC = "asc"
    DESC = "desc"


class TaskSortField(StrEnum):
    DUE_DATE = "dueDate"
    PRIORITY = "priority"
    STATUS = "status"
    CREATED_AT = "createdAt"
