from typing import Annotated

from fastapi import Depends, Request

from src.application.use_cases.change_task_status import ChangeTaskStatus
from src.application.use_cases.create_task import CreateTask
from src.application.use_cases.delete_task import DeleteTask
from src.application.use_cases.get_task import GetTask
from src.application.use_cases.get_task_stats import GetTaskStats
from src.application.use_cases.list_tasks import ListTasks
from src.application.use_cases.update_task import UpdateTask
from src.infrastructure.http.container import Container


def provide_container(request: Request) -> Container:
    return request.app.state.container


ContainerDep = Annotated[Container, Depends(provide_container)]


def provide_create_task(c: ContainerDep) -> CreateTask:
    return CreateTask(c.repository, c.clock, c.scheduler, c.ids)


def provide_get_task(c: ContainerDep) -> GetTask:
    return GetTask(c.repository)


def provide_list_tasks(c: ContainerDep) -> ListTasks:
    return ListTasks(c.repository)


def provide_update_task(c: ContainerDep) -> UpdateTask:
    return UpdateTask(c.repository, c.clock, c.scheduler)


def provide_change_task_status(c: ContainerDep) -> ChangeTaskStatus:
    return ChangeTaskStatus(c.repository, c.clock, c.scheduler)


def provide_delete_task(c: ContainerDep) -> DeleteTask:
    return DeleteTask(c.repository, c.scheduler)


def provide_get_task_stats(c: ContainerDep) -> GetTaskStats:
    return GetTaskStats(c.repository, c.clock)


CreateTaskDep = Annotated[CreateTask, Depends(provide_create_task)]
GetTaskDep = Annotated[GetTask, Depends(provide_get_task)]
ListTasksDep = Annotated[ListTasks, Depends(provide_list_tasks)]
UpdateTaskDep = Annotated[UpdateTask, Depends(provide_update_task)]
ChangeTaskStatusDep = Annotated[ChangeTaskStatus, Depends(provide_change_task_status)]
DeleteTaskDep = Annotated[DeleteTask, Depends(provide_delete_task)]
GetTaskStatsDep = Annotated[GetTaskStats, Depends(provide_get_task_stats)]
