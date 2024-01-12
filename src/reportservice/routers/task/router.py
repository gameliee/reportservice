from datetime import datetime, timedelta
from typing import List
from apscheduler.triggers.cron import CronTrigger
from fastapi import APIRouter, Body, Request, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pymongo.collection import Collection
from pymongo.results import UpdateResult
import apscheduler
from apscheduler.job import Job
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from motor.motor_asyncio import AsyncIOMotorCollection
from ...settings import AppSettings
from ..content.router import get_content
from .models import TaskModelCreate, TaskModelView, TaskModelUpdate, ContentModel, JobModel
from .task import render_and_send_today


async def remove_orphan_jobs(request: Request):
    """
    In each request, find all the job that did not belong to any task, then delete such jobs
    With task whose job is deleted somehow, recreate it here
    """
    app_setting: AppSettings = request.app.config
    colname = app_setting.DB_COLLECTION_TASK
    scheduler: AsyncIOScheduler = request.app.scheduler
    jobs = scheduler.get_jobs()
    # find tasks appropriate to each job. If no task, then detele job
    for job in jobs:
        task = await request.app.mongodb[colname].find_one({"job_id": job.id})
        if task is None:
            scheduler.remove_job(job.id)


router = APIRouter(dependencies=[Depends(remove_orphan_jobs)])


@router.post("/", response_description="Add new task", response_model=TaskModelView)
async def create_task(request: Request, task: TaskModelCreate = Body(...)):
    app_setting: AppSettings = request.app.config
    colname = app_setting.DB_COLLECTION_TASK
    collection: AsyncIOMotorCollection = request.app.mongodb[colname]
    scheduler: AsyncIOScheduler = request.app.scheduler

    # schedule the task
    try:
        cron = CronTrigger.from_crontab(task.trigger)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=f"crontab format error: {e}")

    content = await get_content(request, id=task.content_id)
    content = ContentModel.model_validate(content)

    # always create task in pause state
    task.enable = False

    jobid = str(task.job_id)
    try:
        job: Job = scheduler.add_job(render_and_send_today, cron, [content.id, app_setting], id=jobid)
        assert not job.pending
        job.pause()
    except Exception as e:
        raise e
        # revert
        raise HTTPException(500, detail=f"cannot add job: {e}")

    task_serilzed = jsonable_encoder(task)
    new_task = await collection.insert_one(task_serilzed)
    created_task = await collection.find_one({"_id": new_task.inserted_id})
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=created_task)


@router.get("/", response_description="Get all tasks", response_model=List[TaskModelView])
async def list_tasks(request: Request, offset: int = 0, limit: int = 0):
    app_setting: AppSettings = request.app.config
    colname = app_setting.DB_COLLECTION_TASK
    collection: AsyncIOMotorCollection = request.app.mongodb[colname]
    scheduler: AsyncIOScheduler = request.app.scheduler

    tasks = []
    async for atask in collection.find().skip(offset).limit(limit):
        id = atask["_id"]
        job = scheduler.get_job(atask["job_id"])
        if job is None:
            raise HTTPException(status_code=404, detail=f"In task {id}, Job {atask['job_id']} not found")
        content = await get_content(request, id=atask["content_id"])
        if content is None:
            raise HTTPException(status_code=404, detail=f"In task {id}, Content {atask['content_id']} not found")
        task = TaskModelView(job=JobModel.parse_job(job), content=content, **atask)
        tasks.append(task)
    return tasks


@router.get("/{id}", response_description="Get task with id", response_model=TaskModelView)
async def read_task(request: Request, id):
    app_setting: AppSettings = request.app.config
    colname = app_setting.DB_COLLECTION_TASK
    collection: AsyncIOMotorCollection = request.app.mongodb[colname]
    scheduler: AsyncIOScheduler = request.app.scheduler

    task = await collection.find_one({"_id": id})
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {id} not found")
    job = scheduler.get_job(task["job_id"])
    if job is None:
        raise HTTPException(status_code=404, detail=f"In task {id}, Job {task['job_id']} not found")
    content = await get_content(request, task["content_id"])
    if content is None:
        raise HTTPException(status_code=404, detail=f"In task {id}, Content {task['content_id']} not found")
    task = TaskModelView(job=JobModel.parse_job(job), content=content, **task)
    return task


@router.delete("/{id}", response_description="Detele a task")
async def delete_task(request: Request, id):
    app_setting: AppSettings = request.app.config
    colname = app_setting.DB_COLLECTION_TASK
    collection: AsyncIOMotorCollection = request.app.mongodb[colname]
    scheduler: AsyncIOScheduler = request.app.scheduler

    task = await collection.find_one({"_id": id})
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {id} not found")
    try:
        scheduler.remove_job(task["job_id"])
    except apscheduler.jobstores.base.JobLookupError:
        pass

    delete_result = await collection.delete_one({"_id": id})
    if delete_result.deleted_count == 1:
        return True
    raise HTTPException(status_code=404, detail=f"Task {id} not found")


@router.get("/{id}/pause", response_description="Pause the task")
async def pause_task(request: Request, id):
    app_setting: AppSettings = request.app.config
    colname = app_setting.DB_COLLECTION_TASK
    collection: AsyncIOMotorCollection = request.app.mongodb[colname]
    scheduler: AsyncIOScheduler = request.app.scheduler

    task = await read_task(request, id)
    task = TaskModelView.model_validate(task)

    job: Job = scheduler.get_job(task.job_id)
    job.pause()
    update = {"enable": False}
    update_result: UpdateResult = await collection.update_one({"_id": id}, {"$set": jsonable_encoder(update)})
    if update_result.modified_count == 1:
        """it changed"""
        pass
    return await read_task(request, id)


@router.get("/{id}/resume", response_description="Resume the task")
async def resume_task(request: Request, id):
    app_setting: AppSettings = request.app.config
    colname = app_setting.DB_COLLECTION_TASK
    collection: AsyncIOMotorCollection = request.app.mongodb[colname]
    scheduler: AsyncIOScheduler = request.app.scheduler

    task = await read_task(request, id)
    task = TaskModelView.model_validate(task)

    job: Job = scheduler.get_job(task.job_id)
    job.resume()
    update = {"enable": True}
    update_result: UpdateResult = await collection.update_one({"_id": id}, {"$set": jsonable_encoder(update)})
    if update_result.modified_count == 1:
        """it changed"""
        pass
    return await read_task(request, id)


@router.put("/{id}", response_description="Update a task", response_model=TaskModelView)
async def update_task(request: Request, id, task: TaskModelUpdate):
    app_setting: AppSettings = request.app.config
    colname = app_setting.DB_COLLECTION_TASK
    collection: AsyncIOMotorCollection = request.app.mongodb[colname]
    scheduler: AsyncIOScheduler = request.app.scheduler

    old = await read_task(request, id)
    old = TaskModelView.model_validate(old)

    if task.trigger is not None and task.trigger != old.trigger:
        try:
            cron = CronTrigger.from_crontab(task.trigger)
        except ValueError as e:
            raise HTTPException(status_code=422, detail=f"crontab format error: {e}")
        job: Job = scheduler.get_job(old.job_id)
        job.reschedule(cron)
        await pause_task(request, id)

    task = task.model_dump(exclude_none=True)
    if len(task) >= 1:
        await collection.update_one({"_id": id}, {"$set": jsonable_encoder(task)})
    return await read_task(request, id)


@router.get("/{id}/logs", response_description="Do the task right now")
async def logs_task(
    request: Request, id, since: datetime = datetime.now() - timedelta(days=7), end: datetime = datetime.now()
):
    """get the logs from since to end

    Args:
        request (Request): _description_
        id (_type_): id of the task
        since (datetime): begin
        end (datetime): end
    """
    raise HTTPException(status_code=501, detail="logs_task is not implemented yet")
