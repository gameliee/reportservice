from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter
from .models import LogModel, LogLevelEnum
from ..common import DepLogCollection

router = APIRouter()


@router.get("/", response_model=List[LogModel])
async def list_logs(
    collection: DepLogCollection,
    offset: int = 0,
    limit: int = 0,
    id: Optional[str] = None,
    begin: datetime = datetime.now() - timedelta(days=7),
    end: datetime = datetime.now() + timedelta(days=1),
    level: LogLevelEnum = LogLevelEnum.NOTSET,
):
    """Get logs by time range, level and id"""
    query = {"logtime": {"$gt": begin, "$lte": end}}
    if id is not None:
        query["metadata.uid"] = id
    if level != LogLevelEnum.NOTSET:
        query["metadata.level"] = level.value
    print(query)
    records = []
    async for doc in collection.find(query).skip(offset).limit(limit):
        doc.pop("_id")  # remove _id
        records.append(doc)
    return records
