from pydantic_settings import BaseSettings
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
import pytest


@pytest.fixture(scope="session")
def dbcolelction(dburi, testsettings: BaseSettings) -> AsyncIOMotorCollection:
    mongodb_client = AsyncIOMotorClient(dburi, uuidRepresentation="standard")
    mongodb = mongodb_client[testsettings.DB_NAME]
    collection = mongodb[testsettings.DB_COLLECTION_REPORT]
    return collection
