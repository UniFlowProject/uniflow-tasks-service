from typing import Annotated

from fastapi import APIRouter, Query, Response, status

from src.infrastructure.http.auth import CurrentUser
from src.infrastructure.http.dependencies import (
    ChangeTaskStatusDep,
    CreateTaskDep,
    DeleteTaskDep,
    GetTaskDep,
    GetTaskStatsDep,
    ListTasksDep,
    UpdateTaskDep,
)
from src.infrastructure.http.query import TaskListQuery
from src.infrastructure.http.schemas import (
    ChangeStatusRequest,
    CreateTaskRequest,
    TaskListResponse,
    TaskResponse,
    TaskStatsResponse,
    UpdateTaskRequest,
)

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", status_code=status.HTTP_201_CREATED)
def create_task(
    body: CreateTaskRequest,
    user: CurrentUser,
    use_case: CreateTaskDep,
) -> TaskResponse:
    return TaskResponse.from_task(use_case.execute(user, body.to_command()))


@router.get("")
def list_tasks(
    query: Annotated[TaskListQuery, Query()],
    user: CurrentUser,
    use_case: ListTasksDep,
) -> TaskListResponse:
    return TaskListResponse.from_page(use_case.execute(query.to_filter(user.id)))


# Declared before "/{task_id}" so "stats" is not captured as a task id.
@router.get("/stats")
def get_task_stats(
    user: CurrentUser,
    use_case: GetTaskStatsDep,
) -> TaskStatsResponse:
    return TaskStatsResponse.from_stats(use_case.execute(user))


@router.get("/{task_id}")
def get_task(
    task_id: str,
    user: CurrentUser,
    use_case: GetTaskDep,
) -> TaskResponse:
    return TaskResponse.from_task(use_case.execute(user, task_id))


@router.patch("/{task_id}")
def update_task(
    task_id: str,
    body: UpdateTaskRequest,
    user: CurrentUser,
    use_case: UpdateTaskDep,
) -> TaskResponse:
    return TaskResponse.from_task(use_case.execute(user, task_id, body.to_command()))


@router.patch("/{task_id}/status")
def change_task_status(
    task_id: str,
    body: ChangeStatusRequest,
    user: CurrentUser,
    use_case: ChangeTaskStatusDep,
) -> TaskResponse:
    return TaskResponse.from_task(use_case.execute(user, task_id, body.to_command()))


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: str,
    user: CurrentUser,
    use_case: DeleteTaskDep,
) -> Response:
    use_case.execute(user, task_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
