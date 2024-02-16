from datetime import datetime, timedelta
from logging import Logger
import httpx
from apscheduler.schedulers.base import BaseScheduler
from apscheduler.events import EVENT_JOB_ERROR, JobExecutionEvent
from apscheduler.job import Job
from ...settings import AppSettingsModel
from .models import TaskModelView


async def render_and_send_today(content_id: str, settings: AppSettingsModel, timeout=60, logger: Logger = None):
    params = {"render_date": datetime.now()}
    async with httpx.AsyncClient() as client:
        r = await client.get(
            f"http://localhost:{settings.PORT}/content/{content_id}/render_and_send", params=params, timeout=timeout
        )

    if r.status_code != 200:
        logger.error(
            f"Failed to render and send content {content_id} at {params['render_date']}, status code: {r.status_code}"
        )

    assert (
        r.status_code == 200
    ), f"Failed to render and send content {content_id} at {params['render_date']}, status code: {r.status_code}"
    return r


def retry_a_job(job_id: str, settings: AppSettingsModel, logger: Logger = None):
    # get the task by this job_id
    TIMEOUT = 3
    body = {"job_id": job_id}
    response = httpx.post(f"http://localhost:{settings.PORT}/task/search", json=body, timeout=TIMEOUT)
    tasks = response.json()
    if len(tasks) == 0:
        logger.error("A major problem: there is a orphan job (job_id = %s)", job_id)
        return
    if len(tasks) > 1:
        logger.error("A major problem: there are more than 1 tasks associated with job_id %s", job_id)

    task: TaskModelView = tasks[0]
    logger.debug("The task associated to the job_id %s is %s", job_id, task.id)

    if task.failed_count < task.retries:
        # reschedule this task
        last_run_time = datetime.now()  # TODO: Find a better way to store the last_run_time
        next_run_time = last_run_time + timedelta(task.retries_delay)

        body = {"next_run_time": next_run_time}
        response = httpx.put(f"http://localhost:{settings.PORT}/task/{task.id}", json=body, timeout=TIMEOUT)
        if response.status_code == 200:
            task2: TaskModelView = response.json()
            assert task2.job.next_run_time == next_run_time
            logger.info(f"Task {task.id} will retry at {next_run_time}")
        else:
            logger.error(
                f"Failed to reschedule task {task.id} at {next_run_time}, status code: {response.status_code}, detail: {response.json()}"
            )

        # increase the retries count
        body = {"failed_count": task.failed_count + 1}
        response = httpx.put(f"http://localhost:{settings.PORT}/task/{task.id}", json=body, timeout=TIMEOUT)

    else:
        logger.error("Task %s has reached the maximum retries, will not retry anymore", task.id)


def register_listerner(scheduler: BaseScheduler, settings: AppSettingsModel, logger: Logger = None):
    def error_listener(event: JobExecutionEvent):
        if not event.exception:
            return

        logger.error(f"An error occurred in job: {event.job_id} - {event.exception}")
        retry_a_job(event.job_id, settings, logger)

    scheduler.add_listener(error_listener, EVENT_JOB_ERROR)
