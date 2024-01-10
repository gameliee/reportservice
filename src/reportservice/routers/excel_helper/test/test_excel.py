import pandas as pd
from datetime import datetime
import pytest
from motor.motor_asyncio import AsyncIOMotorDatabase
from ..excel import read_excel_validate, fill_excel, extract_and_fill_excel


def test_input_validate(excelbytes):
    """please manually check the file inputvalidate.xlsx"""
    with open("inputvalidate.xlsx", "wb") as f:
        f.write(excelbytes)


def test_read_excel_validate(excelbytes):
    df = read_excel_validate(excelbytes)
    assert isinstance(df, pd.DataFrame)
    assert len(df.columns) == 8
    assert len(df) == 29


def test_fill_excel_with_content(excelbytes):
    outbytes = fill_excel(excelbytes, pd.DataFrame())
    assert outbytes is None


def test_fill_excel1(excelbytes):
    """please manually check the file inputvalidate.xlsx"""
    df = pd.DataFrame(
        columns=[
            "unnamed: 0",
            "stt",
            "đơn vị",
            "mã nhân viên",
            "họ và tên",
            "ghi nhận lần đầu",
            "ghi nhận lần cuối",
            "trạng thái mẫu",
        ]
    )
    outbytes = fill_excel(excelbytes, df)
    assert outbytes is not None
    with open("out.xlsx", "wb") as f:
        f.write(outbytes)


@pytest.mark.asyncio
async def test_logics(dbinstance, appconfig, test_time, excelbytes):  # noqa: F811
    assert isinstance(dbinstance, AsyncIOMotorDatabase)
    begin, end = test_time
    staff_collection = appconfig.faceiddb.staff_collection
    bodyfacename_collection = appconfig.faceiddb.face_collection
    outbytes = await extract_and_fill_excel(
        dbinstance, staff_collection, bodyfacename_collection, excelbytes, begin, end
    )
    assert outbytes is not None
    with open("out.xlsx", "wb") as f:
        f.write(outbytes)
    # Please open `out.xlsx` an manually check the result
