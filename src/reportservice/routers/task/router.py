from typing import List, Optional, Dict
from fastapi import APIRouter, Body, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pymongo.results import UpdateResult
import apscheduler
from apscheduler.triggers.date import DateTrigger
from apscheduler.schedulers.base import BaseScheduler
from apscheduler.job import Job
from ..models import TaskId
from ..common import DepTaskCollection, DepSCheduler, DepContentCollection, DepAppSettings
from ..content.router import get_content
from .customtriggers import CronTriggerWithHoliday, IntervalTriggerWithHoliday
from .task import render_and_send_today
from .models import (
    TaskModel,
    TaskModelCreate,
    TaskModelView,
    TaskModelUpdate,
    TaskModelSearch,
    JobModel,
    CronTriggerModel,
    IntervalTriggerModel,
    DateTriggerModel,
)


async def remove_orphan_jobs(task_collection: DepTaskCollection, scheduler: DepSCheduler):
    """
    In each request, find all the job that did not belong to any task, then delete such jobs
    With task whose job is deleted somehow, recreate it here
    """
    jobs = scheduler.get_jobs()
    # find tasks appropriate to each job. If no task, then detele job
    for job in jobs:
        task = await task_collection.find_one({"job_id": job.id})
        if task is None:
            scheduler.remove_job(job.id)


router = APIRouter(dependencies=[Depends(remove_orphan_jobs)])
responses = {404: {"description": "No task found"}}


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=TaskModelView)
async def create_task(
    task_collection: DepTaskCollection,
    scheduler: DepSCheduler,
    content_collection: DepContentCollection,
    app_setting: DepAppSettings,
    task: TaskModelCreate = Body(...),
):
    """Create a new task"""
    # schedule the task
    if task.trigger.type == "cron":
        _trigger: CronTriggerModel = task.trigger
        try:
            trigger = CronTriggerWithHoliday.from_crontab(_trigger.cron)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=f"crontab format error: {e}") from e
        trigger.start_date = _trigger.start_date
        trigger.end_date = _trigger.end_date
        trigger.set_exclude_dates(_trigger.exclude_dates)
    elif task.trigger.type == "interval":
        _trigger: IntervalTriggerModel = task.trigger
        trigger = IntervalTriggerWithHoliday(
            seconds=_trigger.interval, start_date=_trigger.start_time, exclude_dates=_trigger.exclude_dates
        )
    elif task.trigger.type == "date":
        _trigger: DateTriggerModel = task.trigger
        trigger = DateTrigger(run_date=_trigger.run_date)
    else:
        raise HTTPException(status_code=422, detail=f"trigger type {task.trigger.type} not supported")

    # must check if this content_id is valid
    content = await get_content(content_collection, id=task.content_id)
    content_id = content["_id"]

    # convert the task to storage model
    storage_task = TaskModel(**task.model_dump())

    # always create task in pause state
    storage_task.enable = False

    jobid = str(storage_task.job_id)

    job: Job = scheduler.add_job(render_and_send_today, trigger, [content_id, app_setting, task.timeout], id=jobid)
    assert not job.pending
    job.pause()  # always pause after create

    task_serilzed = jsonable_encoder(storage_task)
    new_task = await task_collection.insert_one(task_serilzed)
    created_task = await task_collection.find_one({"_id": new_task.inserted_id})
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=created_task)


def doc_to_taskmodel(doc: Dict, scheduler: BaseScheduler) -> TaskModelView:
    """Convert a task document (in the database) to TaskModelView"""
    task = TaskModel.model_validate(doc)
    job: Job = scheduler.get_job(task.job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"In task {task.id}, Job {task.job_id} not found")
    else:
        pass
    view = TaskModelView(job=JobModel.parse_job(job), **doc)
    return view


@router.get("/", response_model=List[TaskModelView])
async def list_tasks(
    task_collection: DepTaskCollection,
    scheduler: DepSCheduler,
    offset: int = 0,
    limit: int = 0,
):
    """Get all tasks"""
    views = []
    async for doc in task_collection.find().skip(offset).limit(limit):
        view = doc_to_taskmodel(doc, scheduler)
        views.append(view)
    return views


@router.post("/search", response_model=List[TaskModelView])
async def search_tasks(
    task_collection: DepTaskCollection,
    scheduler: DepSCheduler,
    search: Optional[TaskModelSearch] = None,
    offset: int = 0,
    limit: int = 0,
):
    """Search tasks by conditions"""
    if search is None:
        return []

    search_condition = search.model_dump(exclude_none=True)
    if not search_condition:  # empty dict
        return []

    views = []
    async for doc in task_collection.find(search_condition).skip(offset).limit(limit):
        view = doc_to_taskmodel(doc, scheduler)
        views.append(view)
    return views


@router.get("/{id}", response_model=TaskModelView, responses=responses)
async def read_task(task_collection: DepTaskCollection, scheduler: DepSCheduler, id: TaskId) -> TaskModelView:
    """Get task with id"""
    doc = await task_collection.find_one({"_id": id})
    if not doc:
        raise HTTPException(status_code=404, detail=f"Task {id} not found")
    view = doc_to_taskmodel(doc, scheduler)
    return view


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={**responses, 204: {"description": "Content has been deleted successfully. No further information"}},
)
async def delete_task(task_collection: DepTaskCollection, scheduler: DepSCheduler, id: TaskId) -> None:
    task = await task_collection.find_one({"_id": id})
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {id} not found")
    try:
        scheduler.remove_job(task["job_id"])
    except apscheduler.jobstores.base.JobLookupError:
        pass

    delete_result = await task_collection.delete_one({"_id": id})
    if delete_result.deleted_count == 1:
        return JSONResponse(status_code=status.HTTP_204_NO_CONTENT, content=f"Task {id} has been deleted")
    raise HTTPException(status_code=404, detail=f"Task {id} not found")


@router.get("/{id}/pause", responses=responses)
async def pause_task(task_collection: DepTaskCollection, scheduler: DepSCheduler, id: TaskId):
    """Pause the task"""
    task = await read_task(task_collection, scheduler, id)
    task = TaskModelView.model_validate(task)

    job: Job = scheduler.get_job(task.job_id)
    job.pause()
    update = {"enable": False}
    update_result: UpdateResult = await task_collection.update_one({"_id": id}, {"$set": jsonable_encoder(update)})
    if update_result.modified_count == 1:
        """it changed"""
        pass
    return await read_task(task_collection, scheduler, id)


@router.get("/{id}/resume", responses=responses)
async def resume_task(task_collection: DepTaskCollection, scheduler: DepSCheduler, id: TaskId):
    """Resume the task"""
    task = await read_task(task_collection, scheduler, id)
    task = TaskModelView.model_validate(task)

    job: Job = scheduler.get_job(task.job_id)
    job.resume()
    update = {"enable": True}
    update_result: UpdateResult = await task_collection.update_one({"_id": id}, {"$set": jsonable_encoder(update)})
    if update_result.modified_count == 1:
        """it changed"""
        pass
    return await read_task(task_collection, scheduler, id)


@router.put("/{id}", response_model=TaskModelView, responses=responses)
async def update_task(
    task_collection: DepTaskCollection,
    scheduler: DepSCheduler,
    id: TaskId,
    task: TaskModelUpdate,
):
    """Update a task. Note that if change the trigger, the task need to be resume again"""
    old = await read_task(task_collection, scheduler, id)
    old = TaskModelView.model_validate(old)

    # schedule the task
    if task.trigger is not None and task.trigger != old.trigger:
        if task.trigger.type == "cron":
            _trigger: CronTriggerModel = task.trigger
            try:
                trigger = CronTriggerWithHoliday.from_crontab(_trigger.cron)
            except ValueError as e:
                raise HTTPException(status_code=422, detail=f"crontab format error: {e}") from e
            trigger.start_date = _trigger.start_date
            trigger.end_date = _trigger.end_date
            trigger.set_exclude_dates(_trigger.exclude_dates)
        elif task.trigger.type == "interval":
            _trigger: IntervalTriggerModel = task.trigger
            trigger = IntervalTriggerWithHoliday(
                seconds=_trigger.interval, start_date=_trigger.start_time, exclude_dates=_trigger.exclude_dates
            )
        elif task.trigger.type == "date":
            _trigger: DateTriggerModel = task.trigger
            trigger = DateTrigger(run_date=_trigger.run_date)
        else:
            raise HTTPException(status_code=422, detail=f"trigger type {task.trigger.type} not supported")

        job: Job = scheduler.get_job(old.job_id)
        job.reschedule(trigger)
        await pause_task(task_collection, scheduler, id)

    if task.next_run_time is not None:
        job: Job = scheduler.get_job(old.job_id)
        job.modify(next_run_time=task.next_run_time)

    task = task.model_dump(exclude_none=True, exclude="next_run_time")  # next_run_time is not in the TaskModel model
    if len(task) >= 1:
        await task_collection.update_one({"_id": id}, {"$set": jsonable_encoder(task)})
    return await read_task(task_collection, scheduler, id)
