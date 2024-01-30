from base64 import b64encode, b64decode
from typing import List, Optional, Annotated
from fastapi import APIRouter, Request, HTTPException, status, UploadFile, File, Response
from datetime import datetime
from pymongo.results import UpdateResult
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from .excel import read_excel_validate, ExcelInvalidException, ExcelColumn
from .models import (
    ContentModelCreate,
    ContentModel,
    ContentModelRendered,
    ContentModelUpdate,
    ContentQueryResult,
    QueryParamters,
)
from .content import render, send, query
from ..common import DepAppConfig, DepContentCollection, DepTaskCollection
from ..common import DepStaffCollection, DepBodyFaceNameCollection, DepLogger
from ..common import DepEmailSpammer

router = APIRouter()


@router.get("/", response_description="Get all contents", response_model=List[ContentModel])
async def list_contents(collection: DepContentCollection, offset: int = 0, limit: int = 0):
    triggers = []
    for doc in await collection.find().skip(offset).limit(limit).to_list(100):
        triggers.append(doc)
    return triggers


@router.get("/{id}", response_description="Get a content by id", response_model=ContentModel)
async def get_content(collection: DepContentCollection, id):
    content = await collection.find_one({"_id": id})
    if content is not None:
        return content

    raise HTTPException(status_code=404, detail=f"Content {id} not found")


@router.post(
    "/",
    description="Create a content without an excel file. Please upload the excel file in another query if needed",
    response_model=ContentModel,
)
async def create_content(collection: DepContentCollection, content: ContentModelCreate):
    if (existed := await collection.find_one({"_id": content.id})) is not None:
        raise HTTPException(status_code=404, detail=f"Content {existed['_id']} existed")

    content = jsonable_encoder(content)
    new_content = await collection.insert_one(content)
    created_content = await collection.find_one({"_id": new_content.inserted_id})

    return JSONResponse(status_code=status.HTTP_201_CREATED, content=created_content)


@router.post(
    "/{id}/upload",
    description="Upload the excel file of the content",
    response_description="return true if wrote to db",
    response_model=bool,
)
async def upload_excel(collection: DepContentCollection, id, excelfile: UploadFile = File(...)):
    """upload the excel file for the content.\n
    NOTE: when upload excel file, the content will update its staff_codes"""
    excel = await excelfile.read()
    # NOTE: check the len, if too large then should not be upload
    max_file_size = 10 * 1024 * 1024  # 10 MB in bytes
    if len(excel) > max_file_size:
        error_message = f"File size exceeds the maximum limit of {max_file_size} bytes."
        raise HTTPException(status_code=413, detail=error_message)

    try:
        df = read_excel_validate(excel)
    except ExcelInvalidException as e:
        raise HTTPException(status_code=400, detail=str(e))

    new_staff_codes = df[ExcelColumn.ESTAFF].dropna().tolist()

    new_query_parameteres = QueryParamters(staffcodes=new_staff_codes)

    base64_str = b64encode(excel).decode("utf-8")
    result = await collection.update_one(
        {"_id": id}, {"$set": {"excel": base64_str, "query_parameters": new_query_parameteres.model_dump()}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail=f"Content {id} not found")

    return result.acknowledged


@router.get("/{id}/download", description="Download the excel file of the content")
async def download_excel(collection: DepContentCollection, id):
    content = await collection.find_one({"_id": id})

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


@router.delete("/{id}", response_description="Delete a content, also delete related tasks")
async def delete_content(content_collection: DepContentCollection, task_collection: DepTaskCollection, id):
    """delete a content which linked with no task. If there are tasks using this content, abort and raise error"""
    # is there any tasks with this id?
    task = await task_collection.find_one({"content_id": id})
    if task is not None:
        raise HTTPException(status_code=400, detail=f"There are tasks using this content, one is {task}")

    delete_result = await content_collection.delete_one({"_id": id})

    if delete_result.deleted_count == 1:
        return JSONResponse(status_code=status.HTTP_200_OK, content=f"Content {id} has been deleted")

    raise HTTPException(status_code=404, detail=f"Content {id} not found")


@router.put("/{id}", response_description="Update a content")
async def update_content(content_collection: DepContentCollection, id, content: ContentModelUpdate):
    # remove None fields
    content = {k: v for k, v in content.model_dump().items() if v is not None}

    if len(content) >= 1:
        update_result: UpdateResult = await content_collection.update_one(
            {"_id": id}, {"$set": jsonable_encoder(content)}
        )
        if update_result.modified_count == 1:
            if (updated_content := await content_collection.find_one({"_id": id})) is not None:
                return updated_content

    if (existing_content := await content_collection.find_one({"_id": id})) is not None:
        return existing_content

    raise HTTPException(status_code=404, detail=f"Content {id} not found")


@router.get("/{id}/query", response_description="Query the content", response_model=ContentQueryResult)
async def query_content(
    content_collection: DepContentCollection,
    app_config: DepAppConfig,
    staff_collection: DepStaffCollection,
    bodyfacename_collection: DepBodyFaceNameCollection,
    logger: DepLogger,
    id: str,
    query_date: Optional[datetime] = None,
):
    """Query the content with the data of query_date, default for today"""
    if query_date is None:
        query_date = datetime.now()
    content = await get_content(content_collection, id=id)
    content = ContentModel.model_validate(content)

    query_result = await query(staff_collection, bodyfacename_collection, content, query_date, logger)

    logger.debug(query_result, extra={"id": id})
    return query_result


@router.get("/{id}/render", response_description="Render the content", response_model=ContentModelRendered)
async def query_render_content(
    content_collection: DepContentCollection,
    app_config: DepAppConfig,
    staff_collection: DepStaffCollection,
    bodyfacename_collection: DepBodyFaceNameCollection,
    logger: DepLogger,
    id: str,
    render_date: Optional[datetime] = None,
):
    """Render the content with the data of render_date, default for today"""
    query_result = await query_content(
        content_collection, app_config, staff_collection, bodyfacename_collection, logger, id, render_date
    )
    content = await get_content(content_collection, id=id)
    content = ContentModel.model_validate(content)
    text = await render(query_result, content)
    return text


@router.get("/{id}/render_and_send", response_description="Render the content, and then send")
async def render_and_send(
    content_collection: DepContentCollection,
    app_config: DepAppConfig,
    staff_collection: DepStaffCollection,
    bodyfacename_collection: DepBodyFaceNameCollection,
    logger: DepLogger,
    spammer_getter: DepEmailSpammer,
    id: str,
    render_date: Optional[datetime] = None,
):
    """Render the content with the data of render_date, then send"""
    if render_date is None:
        render_date = datetime.now()
    text = await query_render_content(
        content_collection, app_config, staff_collection, bodyfacename_collection, logger, id, render_date
    )

    spammer = spammer_getter()
    ret = await send(text, spammer)
    logger.info(ret, extra={"id": id})
    return ret
