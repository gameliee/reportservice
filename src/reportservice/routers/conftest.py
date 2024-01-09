from pydantic_settings import BaseSettings
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection, AsyncIOMotorDatabase
import pytest
from .config.conftest import appconfig


@pytest.fixture
def dbinstance(dburi, testsettings: BaseSettings) -> AsyncIOMotorDatabase:
    mongodb_client = AsyncIOMotorClient(dburi, uuidRepresentation="standard")
    mongodb: AsyncIOMotorDatabase = mongodb_client[testsettings.DB_NAME]
    return mongodb
