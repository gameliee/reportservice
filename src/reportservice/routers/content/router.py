from base64 import b64encode, b64decode
from typing import List, Optional
from fastapi import APIRouter, Request, HTTPException, status, UploadFile, File, Response
from datetime import datetime
from pymongo.collection import Collection
from pymongo.results import UpdateResult
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from .models import (
    ContentModelCreate,
    ContentModel,
    ContentModelRendered,
    ContentModelUpdate
)
from .content import render, send
from ..config.router import get_postgres_db, get_spammer

router = APIRouter()
COLNAME = COLCONTENT


@router.get("/", response_description="Get all contents", response_model=List[ContentModel])
async def list_contents(request: Request, offset: int = 0, limit: int = 0):
    triggers = []
    for doc in await request.app.mongodb[COLNAME].find().skip(offset).limit(limit).to_list(100):
        triggers.append(doc)
    return triggers


@router.get("/{id}", response_description="Get a content by id", response_model=ContentModel)
async def get_content(request: Request, id):
    content = await request.app.mongodb[COLNAME].find_one({"_id": id})
    if content is not None:
        return content

    raise HTTPException(status_code=404, detail=f"Content {id} not found")


@router.post(
    "/",
    description="Create a content, without the excel file. Please upload the excel file in another query",
    response_model=ContentModel,
)
async def create_content(request: Request, content: ContentModelCreate):
    if (existed := await request.app.mongodb[COLNAME].find_one({"_id": content.id})) is not None:
        raise HTTPException(status_code=404, detail=f"Content {existed['_id']} existed")

    content = jsonable_encoder(content)
    new_content = await request.app.mongodb[COLNAME].insert_one(content)
    created_content = await request.app.mongodb[COLNAME].find_one({"_id": new_content.inserted_id})

    return JSONResponse(status_code=status.HTTP_201_CREATED, content=created_content)


@router.post(
    "/{id}/upload",
    description="Upload the excel file of the content",
    response_description="return true if wrote to db",
    response_model=bool,
)
async def upload_excel(request: Request, id, excelfile: UploadFile = File(...)):
    excel = await excelfile.read()
    # NOTE: check the len, if too large then should not be upload
    max_file_size = 10 * 1024 * 1024  # 10 MB in bytes
    if len(excel) > max_file_size:
        error_message = f"File size exceeds the maximum limit of {max_file_size} bytes."
        raise HTTPException(status_code=413, detail=error_message)

    base64_str = b64encode(excel).decode("utf-8")
    result = await request.app.mongodb[COLNAME].update_one({"_id": id}, {"$set": {"excel": base64_str}})

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail=f"Content {id} not found")

    return result.acknowledged


@router.get("/{id}/download", description="Download the excel file of the content")
async def download_excel(request: Request, id):
    content = await request.app.mongodb[COLNAME].find_one({"_id": id})

    if content is None:
        raise HTTPException(status_code=404, detail=f"Content {id} not found")

    if "excel" not in content:
        raise HTTPException(status_code=404, detail=f"The content {id} do not have excel")

    excel_bytes = b64decode(str(content["excel"]).encode("utf-8"))
    response = Response(content=excel_bytes, media_type="application/octet-stream")

    # Set the Content-Disposition header to suggest a filename
    filename = "data.xlsx"
    response.headers["Content-Disposition"] = f'attachment; filename="{filename}"'

    return response


@router.delete("/{id}", response_description="Delete a content")
async def delete_content(request: Request, id):
    """delete a content which linked with no task. If there are tasks using this content, abort and raise error"""
    # is there any tasks with this id?
    task = await request.app.mongodb[COLTASKS].find_one({"content_id": id})
    if task is not None:
        raise HTTPException(status_code=400, detail=f"There are tasks using this content, one is {task}")

    delete_result = await request.app.mongodb[COLNAME].delete_one({"_id": id})

    if delete_result.deleted_count == 1:
        return JSONResponse(status_code=status.HTTP_200_OK, content=f"Content {id} has been deleted")

    raise HTTPException(status_code=404, detail=f"Content {id} not found")


@router.put("/{id}", response_description="Update a content")
async def update_content(request: Request, id, content: ContentModelUpdate):
    # remove None fields
    content = {k: v for k, v in content.model_dump().items() if v is not None}

    collection: Collection[ContentModel] = request.app.mongodb[COLNAME]

    if len(content) >= 1:
        update_result: UpdateResult = await collection.update_one({"_id": id}, {"$set": jsonable_encoder(content)})
        if update_result.modified_count == 1:
            if (updated_content := await collection.find_one({"_id": id})) is not None:
                return updated_content

    if (existing_content := await collection.find_one({"_id": id})) is not None:
        return existing_content

    raise HTTPException(status_code=404, detail=f"Content {id} not found")


@router.get("/{id}/render", response_description="Render the content", response_model=ContentModelRendered)
async def render_content(request: Request, id: str, render_date: Optional[datetime] = None):
    """Render the content with the data of render_date, default for today"""
    if render_date is None:
        render_date = datetime.now()
    content = await get_content(request=request, id=id)
    content = ContentModel.model_validate(content)

    # on-demaned connection get
    async with get_postgres_db(request) as db:
        try:
            text = await render(db, content, render_date)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_417_EXPECTATION_FAILED, detail=str(e))

    request.app.logger.info(text, extra={"id": id})
    return text


@router.get("/{id}/render_and_send", response_description="Render the content, and then send")
async def render_and_send(request: Request, id: str, render_date: Optional[datetime] = None):
    """Render the content with the data of render_date, then send"""
    if render_date is None:
        render_date = datetime.now()
    text = await render_content(request, id, render_date)

    async with get_spammer(request) as spammer:
        ret = await send(text, spammer)

    request.app.logger.info(ret, extra={"id": id})
    return ret
