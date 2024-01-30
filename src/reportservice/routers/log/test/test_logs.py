import pytest
import logging
import datetime
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

    async def test_mongo_handler_complex_message(self, log_collection: AsyncIOMotorCollection):
        pipeline = [
            {
                "$match": {
                    "$or": [
                        {"staff_code": {"$in": ["218777"]}},
                        {"full_name": {"$in": []}},
                        {"unit": {"$in": []}},
                        {"department": {"$in": []}},
                        {"title": {"$in": []}},
                        {"email": {"$in": []}},
                        {"cellphone": {"$in": []}},
                        {"$expr": {"$or": []}},
                    ]
                }
            },
            {
                "$lookup": {
                    "from": "BodyFaceName",
                    "let": {"staff_code_var": "$staff_code"},
                    "as": "found",
                    "pipeline": [
                        {
                            "$match": {
                                "$expr": {
                                    "$and": [
                                        {"$eq": ["$staff_id", "$$staff_code_var"]},
                                        {
                                            "$gte": [
                                                "$image_time",
                                                datetime.datetime(2023, 12, 27, 0, 0),
                                            ]
                                        },
                                        {
                                            "$lte": [
                                                "$image_time",
                                                datetime.datetime(2024, 12, 27, 23, 59, 59, 999000),
                                            ]
                                        },
                                        {"$gte": ["$face_reg_score", 0.0]},
                                        {"$eq": ["$has_mask", False]},
                                    ]
                                }
                            }
                        },
                        {"$project": {"staff_id": 1, "image_time": 1}},
                        {"$sort": {"image_time": 1}},
                        {
                            "$group": {
                                "_id": "$staff_id",
                                "firstDocument": {"$first": "$image_time"},
                                "lastDocument": {"$last": "$image_time"},
                            }
                        },
                    ],
                }
            },
            {"$unwind": {"path": "$found", "includeArrayIndex": "arrayIndex", "preserveNullAndEmptyArrays": True}},
            {
                "$project": {
                    "_id": 0,
                    "staff_code": "$staff_code",
                    "full_name": 1,
                    "sex": 1,
                    "cellphone": 1,
                    "email": 1,
                    "unit": 1,
                    "department": 1,
                    "title": 1,
                    "sample_state": 1,
                    "working_state": 1,
                    "first_record": "$found.firstDocument",
                    "last_record": "$found.lastDocument",
                }
            },
        ]
        # Create an instance of MongoHandler
        assert isinstance(log_collection, AsyncIOMotorCollection)
        mongo_handler = MongoHandler(log_collection, self.loop)

        formatter = logging.Formatter("[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s")
        mongo_handler.setFormatter(formatter)

        # Create a log record
        log_record = logging.LogRecord(
            name="test_logger",
            level=logging.INFO,
            pathname="/path/to/file.py",
            lineno=10,
            msg=pipeline,
            args=None,
            exc_info=None,
        )

        # Emit the log record
        mongo_handler.emit(log_record)

        logger = logging.getLogger("just for test")
        logger.addHandler(mongo_handler)
        logger.debug("running the pipeline", pipeline)
