"""Healthcheck module as required"""
import os
import psutil
from enum import Enum
from pydantic import BaseModel, Field
from fastapi import FastAPI


class ServiceStatus(str, Enum):
    UP = "UP"  # running without any errors
    DOWN = "DOWN"  # running with errors


class SystemInfo(BaseModel):
    cpu_used: float = Field(..., description="CPU usages in percentage (%)")
    mem_used: int = Field(..., description="Memory usage in Kilobytes (Kb)")
    mem_max: int = Field(..., description="Maximum capacity of memory in Kilobytes (Kb)")


class CheckData(BaseModel):
    system_info: SystemInfo
    detail: str = Field(
        ...,
        description="Detailed status of service (Exp: service is running/ service disconnected from DB/ service is running with 12 camera...",
    )


class CheckInfo(BaseModel):
    status: ServiceStatus = Field(
        ...,
        description="Status of the service. Could be ON, mean running without any erorrs, or DOWN, mean running with errors",
    )
    data: CheckData


class HealthCheck(BaseModel):
    name: str = Field(..., description="Name of the service")
    version: str = Field(..., description="Version of the service")
    checks: CheckInfo


async def logic_healthcheck(app: FastAPI) -> HealthCheck:
    pid = os.getpid()
    process = psutil.Process(pid)
    memory_info = process.memory_info()

    sysinfo = SystemInfo(
        cpu_used=psutil.cpu_percent(),
        mem_used=memory_info.rss / 1024,
        mem_max=psutil.virtual_memory().total / 1024,
    )
    status: ServiceStatus = ServiceStatus.UP
    detail = "Service is running without any errors."
    try:
        await app.mongodb_client.server_info()
    except Exception as e:
        status = ServiceStatus.DOWN
        detail = f"Service has disconnected from DB, error: {str(e)}"

    checks = CheckInfo(status=status, data=CheckData(system_info=sysinfo, detail=detail))

    healthcheck = HealthCheck(name="reportservice", version="0.4.1", checks=checks)

    return healthcheck
