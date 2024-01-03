import os
import logging
import psutil
import threading
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .settings import settings
from . import customlog


# Global dependency
async def log_everythings(request: Request):
    logger = request.app.logger
    if "id" in request.path_params:
        logger.info(f"Received request: {request.method} {request.url}", extra={"id": request.path_params["id"]})
    else:
        logger.info(f"Received request: {request.method} {request.url}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """manage the database connection, the scheduler using lifespan"""
    app.logger = logging.getLogger(settings.APP_NAME)
    yield


app = FastAPI(lifespan=lifespan, dependencies=[Depends(log_everythings)])
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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


@app.get("/version")
async def version():
    return JSONResponse(status_code=status.HTTP_200_OK, content={"version": "0.0.1"})
