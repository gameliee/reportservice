import pytest
import logging
import asyncio
import pytest_asyncio
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection
from ..logs import MongoHandler, create_log_collection
from ....settings import AppSettingsModel


@pytest.mark.usefixtures("dburi", "testsettings")
@pytest.mark.asyncio(scope="class")
class TestLogger:
    loop: asyncio.AbstractEventLoop

    async def test_remember_loop(self):
        TestLogger.loop = asyncio.get_running_loop()

    async def test_assert_same_loop(self):
        assert asyncio.get_running_loop() is TestLogger.loop

    @pytest_asyncio.fixture(scope="class")
    async def log_collection(self, dburi: str, testsettings: AppSettingsModel):
        assert isinstance(testsettings, AppSettingsModel)
        assert isinstance(dburi, str)
        mongo = AsyncIOMotorClient(dburi, uuidRepresentation="standard")
        database = mongo[testsettings.DB_REPORT_NAME]
        log_collection = await create_log_collection(testsettings.DB_COLLECTION_LOG, database)
        assert isinstance(log_collection, AsyncIOMotorCollection)
        assert log_collection.name == testsettings.DB_COLLECTION_LOG
        yield log_collection
        await log_collection.drop()

    async def test_mongo_handler(self, log_collection: AsyncIOMotorCollection):
        # Create an instance of MongoHandler
        assert isinstance(log_collection, AsyncIOMotorCollection)
        mongo_handler = MongoHandler(log_collection, self.loop)

        # Create a log record
        log_record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/path/to/file.py",
            lineno=10,
            msg="Test log message",
            args=None,
            exc_info=None,
        )

        # Emit the log record
        mongo_handler.emit(log_record)

        await asyncio.sleep(1)

        # Retrieve the log from the collection
        logs = await log_collection.find().to_list(length=None)

        # Assert that the log record is stored in the collection
        assert len(logs) == 1

        log_record.id = "log_test_id"
        mongo_handler.emit(log_record)
        await asyncio.sleep(1)

        # retrieve the latest log from the collection
        logs = await log_collection.find().to_list(length=None)
        assert len(logs) == 2
