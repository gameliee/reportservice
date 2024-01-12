import os
import logging
import psutil
import threading
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from apscheduler.jobstores.mongodb import MongoDBJobStore
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from .settings import settings
from . import customlog

from .routers.stat.retrieval import router as stat_router
from .routers.config.router import router as config_router
from .routers.content.router import router as content_router
from .routers.task.router import router as task_router


# Global dependency
async def log_everythings(request: Request):
    logger = request.app.logger
    if "id" in request.path_params:
        logger.info(f"Received request: {request.method} {request.url}", extra={"id": request.path_params["id"]})
    else:
        logger.info(f"Received request: {request.method} {request.url}")


async def init_configurations(app: FastAPI):
    """init the configurations"""
    app.logger.info("Loading configurations...")
    app.config = settings


async def init_database(app: FastAPI):
    """init the database connection"""
    app.logger.info("Connecting to database...")
    app.mongodb_client = AsyncIOMotorClient(settings.DB_URL, uuidRepresentation="standard")
    app.mongodb: AsyncIOMotorDatabase = app.mongodb_client[settings.DB_NAME]


async def close_database(app: FastAPI):
    """close the database connection"""
    app.logger.info("Closing database connection...")
    app.mongodb_client.close()


async def init_scheduler(app: FastAPI):
    """init scheduler instance"""
    jobstores = {
        "default": MongoDBJobStore(
            database=settings.DB_NAME, collection=settings.DB_COLLECTION_SCHEDULER, host=settings.DB_URL
        ),
    }
    job_defaults = {
        "coalesce": True,  # whether to only run the job once when several run times are due
        "max_instances": 10,
    }

    app.scheduler = AsyncIOScheduler(jobstores=jobstores, job_defaults=job_defaults)
    app.scheduler.start()


async def close_scheduler(app: FastAPI):
    """close the scheduler"""
    app.scheduler: AsyncIOScheduler
    app.scheduler.shutdown()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """manage the database connection, the scheduler using lifespan"""
    app.logger = logging.getLogger(settings.APP_NAME)
    await init_configurations(app)
    await init_database(app)
    await init_scheduler(app)
    yield
    await close_database(app)
    await close_scheduler(app)


app = FastAPI(lifespan=lifespan, dependencies=[Depends(log_everythings)])
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(stat_router, prefix="/stat", tags=["stat"])
app.include_router(config_router, prefix="/config", tags=["config"])
app.include_router(content_router, prefix="/content", tags=["content"])
app.include_router(task_router, prefix="/task", tags=["task"])


@app.get("/")
async def healthcheck():
    pid = os.getpid()
    process = psutil.Process(pid)
    memory_info = process.memory_info()
    thread_count = threading.active_count()

    return {
        "pid": pid,
        "Memory Usage": f"{memory_info.rss / 1024:.2f} KB",
        "Thread Count": f"{thread_count}",
    }


@app.get("/connection-status")
async def connection_status():
    try:
        await app.mongodb_client.server_info()
        return JSONResponse(status_code=status.HTTP_200_OK, content={"status": "Connected"})
    except Exception as e:
        raise e
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"status": "Disconnected", "error": str(e)}
        )


@app.get("/version")
async def version():
    return JSONResponse(status_code=status.HTTP_200_OK, content={"version": "0.0.1"})
