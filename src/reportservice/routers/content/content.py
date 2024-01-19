from base64 import b64encode, b64decode
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorCollection
from ..stat import get_people_count, get_inout_count, get_has_sample_count, get_people_inout
from ..common import EmailSpammer
from .excel import fill_personinout_to_excel, excel_to_html, convert_personinout_to_excel
from .models import ContentModel, ContentModelRendered, ContentQueryResult


def get_weekday_vn(today):
    vn_name = ["hai", "ba", "tư", "năm", "sáu", "bảy", "chủ nhật"]
    return vn_name[today.isoweekday() - 1]


def get_weekday_Vn(today):
    vn_name = ["Hai", "Ba", "Tư", "Năm", "Sáu", "Bảy", "Chủ Nhật"]
    return vn_name[today.isoweekday() - 1]


async def query(
    staff_collection: AsyncIOMotorCollection,
    bodyfacename_collection: AsyncIOMotorCollection,
    content: ContentModel,
    query_date: datetime,
) -> ContentQueryResult:
    day_begin = datetime.combine(date=query_date.date(), time=datetime.min.time())
    day_end = datetime.combine(date=query_date.date(), time=datetime.max.time())
    in_begin = datetime.combine(date=query_date.date(), time=content.checkin_begin.time())
    in_end = in_begin + content.checkin_duration
    out_begin = datetime.combine(date=query_date.date(), time=content.checkout_begin.time())
    out_end = out_begin + content.checkout_duration
    people_count = await get_people_count(staff_collection, day_begin, day_end)
    # has_sample_count = get_has_sample_count(db, staff_collection, bodyfacename_collection, day_begin, day_end), # FIXME:
    checkin_count = await get_inout_count(bodyfacename_collection, in_begin, in_end)
    checkout_count = await get_inout_count(bodyfacename_collection, out_begin, out_end)
    total_count = await get_inout_count(
        bodyfacename_collection, day_begin, day_end
    )  # BUG: this is not correct, change to begin of the day to end of the day

    people_inout = await get_people_inout(
        staff_collection, bodyfacename_collection, content.query_parameters, day_begin, day_end
    )

    return ContentQueryResult(
        query_time=query_date,
        people_count=people_count,
        checkin_count=checkin_count,
        checkout_count=checkout_count,
        total_count=total_count,
        people_inout=people_inout,
    )


async def render(
    query_result: ContentQueryResult,
    content: ContentModel,
) -> ContentModelRendered:
    """render the content to a ContentModelRendered"""

    data = {  # noqa: F841
        "year": query_result.query_time.year,
        "month": query_result.query_time.month,
        "date": query_result.query_time.day,
        "hour": query_result.query_time.hour,
        "min": query_result.query_time.minute,
        "sec": query_result.query_time.second,
        "weekday_vn": get_weekday_vn(query_result.query_time),
        "weekday_Vn": get_weekday_Vn(query_result.query_time),
        "people_count": query_result.people_count,
        # "has_sample_count": query_result.has
        "checkin_count": query_result.checkin_count,
        "checkout_count": query_result.checkout_count,
        "total_count": query_result.total_count,
        "people_inout": query_result.people_inout,
        "table": "",
    }

    # convert query_result.people_inout to excel table
    excel_bytes = b64decode(str(content.excel).encode("utf-8"))  # noqa: F841
    fill_excel_bytes = None
    if content.is_excel_uploaded():
        fill_excel_bytes = fill_personinout_to_excel(query_result.people_inout, excel_bytes)
        html = excel_to_html(fill_excel_bytes)
        data["table"] = html
    else:
        fill_excel_bytes = convert_personinout_to_excel(query_result.people_inout)
        html = excel_to_html(fill_excel_bytes)
        data["table"] = html

    to = ",".join(content.to)
    cc = ",".join(content.cc)
    bcc = ",".join(content.bcc)
    subject = content.get_subject_template().render(data)
    body = content.get_body_template().render(data)

    out = ContentModelRendered(to=to, cc=cc, bcc=bcc, subject=subject, body=body)

    if content.attach is True and fill_excel_bytes is not None:
        filename = content.get_attach_name_template().render(data)
        b64_str = b64encode(fill_excel_bytes).decode("utf-8")
        out.attach = b64_str
        out.attach_name = filename

    return out


async def send(contentrenderd: ContentModelRendered, spammer: EmailSpammer):
    """if sent, return the sent content, if not, return none"""
    if spammer is None:
        return None

    if contentrenderd.attach is not None and contentrenderd.attach_name is not None:
        excel_bytes = b64decode(contentrenderd.attach.encode("utf-8"))
        excel_name = contentrenderd.attach_name
        ret = spammer.send(
            to=contentrenderd.to,
            cc=contentrenderd.cc,
            bcc=contentrenderd.bcc,
            subject=contentrenderd.subject,
            body=contentrenderd.body,
            attachment_filename=excel_name,
            attachment_data=excel_bytes,
        )
    else:
        ret = spammer.send(
            to=contentrenderd.to,
            cc=contentrenderd.cc,
            bcc=contentrenderd.bcc,
            subject=contentrenderd.subject,
            body=contentrenderd.body,
            attachment_filename=None,
        )

    return ret
