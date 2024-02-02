from typing import List
from apscheduler.triggers.date import DateTrigger
from fastapi import APIRouter, Body, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pymongo.results import UpdateResult
import apscheduler
from apscheduler.job import Job
from ..models import CronTriggerModel, IntervalTriggerModel, DateTriggerModel, TaskId
from ..common import DepTaskCollection, DepSCheduler, DepContentCollection, DepAppSettings
from ..content.router import get_content
from .customtriggers import CronTriggerWithHoliday, IntervalTriggerWithHoliday
from .task import render_and_send_today
from .models import TaskModelCreate, TaskModelView, TaskModelUpdate, ContentModel, JobModel


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


@router.post("/", response_description="Add new task", response_model=TaskModelView)
async def create_task(
    task_collection: DepTaskCollection,
    scheduler: DepSCheduler,
    content_collection: DepContentCollection,
    app_setting: DepAppSettings,
    task: TaskModelCreate = Body(...),
):
    # schedule the task
    if task.trigger.type == "cron":
        _trigger: CronTriggerModel = task.trigger
        try:
            trigger = CronTriggerWithHoliday.from_crontab(_trigger.cron)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=f"crontab format error: {e}")
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

    content = await get_content(content_collection, id=task.content_id)
    content = ContentModel.model_validate(content)

    # always create task in pause state
    task.enable = False

    jobid = str(task.job_id)

    job: Job = scheduler.add_job(render_and_send_today, trigger, [content.id, app_setting, _trigger.timeout], id=jobid)
    assert not job.pending
    job.pause()  # always pause after create

    task_serilzed = jsonable_encoder(task)
    new_task = await task_collection.insert_one(task_serilzed)
    created_task = await task_collection.find_one({"_id": new_task.inserted_id})
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=created_task)


@router.get("/", response_description="Get all tasks", response_model=List[TaskModelView])
async def list_tasks(
    task_collection: DepTaskCollection,
    scheduler: DepSCheduler,
    content_collection: DepContentCollection,
    offset: int = 0,
    limit: int = 0,
):
    tasks = []
    async for atask in task_collection.find().skip(offset).limit(limit):
        id = atask["_id"]
        job = scheduler.get_job(atask["job_id"])
        if job is None:
            raise HTTPException(status_code=404, detail=f"In task {id}, Job {atask['job_id']} not found")
        content = await get_content(content_collection, id=atask["content_id"])
        if content is None:
            raise HTTPException(status_code=404, detail=f"In task {id}, Content {atask['content_id']} not found")
        task = TaskModelView(job=JobModel.parse_job(job), content=content, **atask)
        tasks.append(task)
    return tasks


@router.get("/{id}", response_description="Get task with id", response_model=TaskModelView)
async def read_task(
    task_collection: DepTaskCollection, scheduler: DepSCheduler, content_collection: DepContentCollection, id: TaskId
):
    task = await task_collection.find_one({"_id": id})
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {id} not found")
    job = scheduler.get_job(task["job_id"])
    if job is None:
        raise HTTPException(status_code=404, detail=f"In task {id}, Job {task['job_id']} not found")
    content = await get_content(content_collection, task["content_id"])
    if content is None:
        raise HTTPException(status_code=404, detail=f"In task {id}, Content {task['content_id']} not found")
    task = TaskModelView(job=JobModel.parse_job(job), content=content, **task)
    return task


@router.delete("/{id}", response_description="Detele a task")
async def delete_task(task_collection: DepTaskCollection, scheduler: DepSCheduler, id: TaskId):
    task = await task_collection.find_one({"_id": id})
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {id} not found")
    try:
        scheduler.remove_job(task["job_id"])
    except apscheduler.jobstores.base.JobLookupError:
        pass

    delete_result = await task_collection.delete_one({"_id": id})
    if delete_result.deleted_count == 1:
        return True
    raise HTTPException(status_code=404, detail=f"Task {id} not found")


@router.get("/{id}/pause", response_description="Pause the task")
async def pause_task(
    task_collection: DepTaskCollection, scheduler: DepSCheduler, content_collection: DepContentCollection, id: TaskId
):
    task = await read_task(task_collection, scheduler, content_collection, id)
    task = TaskModelView.model_validate(task)

    job: Job = scheduler.get_job(task.job_id)
    job.pause()
    update = {"enable": False}
    update_result: UpdateResult = await task_collection.update_one({"_id": id}, {"$set": jsonable_encoder(update)})
    if update_result.modified_count == 1:
        """it changed"""
        pass
    return await read_task(task_collection, scheduler, content_collection, id)


@router.get("/{id}/resume", response_description="Resume the task")
async def resume_task(
    task_collection: DepTaskCollection, scheduler: DepSCheduler, content_collection: DepContentCollection, id: TaskId
):
    task = await read_task(task_collection, scheduler, content_collection, id)
    task = TaskModelView.model_validate(task)

    job: Job = scheduler.get_job(task.job_id)
    job.resume()
    update = {"enable": True}
    update_result: UpdateResult = await task_collection.update_one({"_id": id}, {"$set": jsonable_encoder(update)})
    if update_result.modified_count == 1:
        """it changed"""
        pass
    return await read_task(task_collection, scheduler, content_collection, id)


@router.put("/{id}", response_description="Update a task", response_model=TaskModelView)
async def update_task(
    task_collection: DepTaskCollection,
    scheduler: DepSCheduler,
    content_collection: DepContentCollection,
    id: TaskId,
    task: TaskModelUpdate,
):
    old = await read_task(task_collection, scheduler, content_collection, id)
    old = TaskModelView.model_validate(old)

    # schedule the task
    if task.trigger is not None and task.trigger != old.trigger:
        if task.trigger.type == "cron":
            _trigger: CronTriggerModel = task.trigger
            try:
                trigger = CronTriggerWithHoliday.from_crontab(_trigger.cron)
            except ValueError as e:
                raise HTTPException(status_code=422, detail=f"crontab format error: {e}")
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
        await pause_task(task_collection, scheduler, content_collection, id)

    task = task.model_dump(exclude_none=True)
    if len(task) >= 1:
        await task_collection.update_one({"_id": id}, {"$set": jsonable_encoder(task)})
    return await read_task(task_collection, scheduler, content_collection, id)
