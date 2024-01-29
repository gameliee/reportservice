import logging
import asyncio
import time
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection, AsyncIOMotorDatabase
from .models import LogModel, LogMeta, LogLevelEnum
from ...settings import AppSettingsModel


async def create_log_collection(collection_name: str, db: AsyncIOMotorDatabase):
    """create a log collection in the database"""
    if collection_name not in await db.list_collection_names():
        col = await db.create_collection(
            collection_name,
            timeseries={"timeField": "logtime", "metaField": "metadata", "granularity": "seconds"},
            expireAfterSeconds=30 * 86400,  # 30 days
        )
    else:
        col = db[collection_name]
    assert isinstance(col, AsyncIOMotorCollection)
    return col


async def writelog(_collection: AsyncIOMotorCollection, _log: LogModel):
    await _collection.insert_one(_log.myencode())


class MongoHandler(logging.Handler):
    """
    A class which asynchronous sends records to a mongodb server timeseries database,
    inspired from HTTPHandler
    """

    def __init__(self, collection: AsyncIOMotorCollection, loop: asyncio.AbstractEventLoop):
        """
        db is a pymongo db class
        """
        logging.Handler.__init__(self)
        self.formatter = logging.Formatter(
            "[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s"
        )
        assert isinstance(collection, AsyncIOMotorCollection)
        assert isinstance(loop, asyncio.AbstractEventLoop)
        self.collection = collection
        self.loop = loop

    def emit(self, record: logging.LogRecord):
        msg = self.format(record)

        record.asctime
        record.name

        print(LogLevelEnum(record.levelno))
        logmeta = LogMeta(level=LogLevelEnum(record.levelno))
        if hasattr(record, "id"):
            logmeta.uid = record.id

        log = LogModel(
            logtime=datetime.fromisoformat(record.asctime.replace(",", ".")),
            metadata=logmeta,
            message=msg,
        )

        self.loop.create_task(writelog(self.collection, log), name="write logs to db")

    # def close(self):
    #     # just wait for the task to finish
    #     self.loop.create_task(asyncio.sleep(1), name="wait for all logs done")
    #     time.sleep(1)
    #     super().close()
