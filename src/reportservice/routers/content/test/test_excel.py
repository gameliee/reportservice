import pandas as pd
from datetime import datetime
import pytest
from ...stat import PersonInoutCollection, PersonInout
from ..excel import (
    read_excel_validate,
    fill_excel,
    fill_personinout_to_excel,
    convert_personinout_to_excel,
    excel_to_html,
)


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


@pytest.fixture
def some_personinout() -> PersonInoutCollection:
    inout = PersonInoutCollection(
        count=4,
        values=[
            PersonInout(
                staff_code="206424",
                sample_state="ready_to_checkin_checkout",
                first_record=datetime(2021, 1, 1),
                last_record=datetime(2021, 1, 1),
                working_state="zombie",
            ),
            PersonInout(
                staff_code="220560",
                sample_state="ready_to_checkin_checkout",
                first_record=datetime(2021, 1, 1),
                last_record=datetime(2021, 1, 1),
                working_state="zombie",
            ),
            PersonInout(
                staff_code="207745",
                sample_state="ready_to_checkin_checkout",
                first_record=datetime(2021, 1, 1),
                last_record=datetime(2021, 1, 1),
                working_state="zombie",
            ),
            PersonInout(
                staff_code="250753",
                sample_state="ready_to_checkin_checkout",
                first_record=datetime(2021, 1, 1),
                last_record=datetime(2021, 1, 1),
                working_state="zombie",
            ),
        ],
    )
    return inout


def test_fill_personinout_to_excel(excelbytes, some_personinout: PersonInoutCollection):
    fill_personinout_to_excel(some_personinout, excelbytes)


def test_convert_personinout_to_excel(some_personinout: PersonInoutCollection):
    outbytes = convert_personinout_to_excel(some_personinout)
    with open("convert.xlsx", "wb") as f:
        f.write(outbytes)

    with open("convert.html", "w") as f:
        f.write(excel_to_html(outbytes))
