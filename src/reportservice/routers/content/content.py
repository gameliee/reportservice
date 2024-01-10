from base64 import b64encode, b64decode
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorDatabase
from ..stat import get_people_count, get_inout_count, get_has_sample_count
from ..excel_helper import extract_and_fill_excel, excel_to_html
from .models import ContentModel, ContentModelRendered
from ..config.email_spammer import EmailSpammer


def get_weekday_vn(today):
    vn_name = ["hai", "ba", "tư", "năm", "sáu", "bảy", "chủ nhật"]
    return vn_name[today.isoweekday() - 1]


def get_weekday_Vn(today):
    vn_name = ["Hai", "Ba", "Tư", "Năm", "Sáu", "Bảy", "Chủ Nhật"]
    return vn_name[today.isoweekday() - 1]


async def render(
    db: AsyncIOMotorDatabase,
    staff_collection: str,
    bodyfacename_collection: str,
    content: ContentModel,
    render_date: datetime,
) -> ContentModelRendered:
    """render the content to a ContentModelRendered"""
    day_begin = datetime.combine(date=render_date.date(), time=datetime.min.time())
    day_end = datetime.combine(date=render_date.date(), time=datetime.max.time())
    in_begin = datetime.combine(date=render_date.date(), time=content.checkin_begin.time())
    in_end = in_begin + content.checkin_duration
    out_begin = datetime.combine(date=render_date.date(), time=content.checkout_begin.time())
    out_end = out_begin + content.checkout_duration

    data = {  # noqa: F841
        "year": render_date.year,
        "month": render_date.month,
        "date": render_date.day,
        "hour": render_date.hour,
        "min": render_date.minute,
        "sec": render_date.second,
        "weekday_vn": get_weekday_vn(render_date),
        "weekday_Vn": get_weekday_Vn(render_date),
        "people_count": await get_people_count(db, staff_collection, bodyfacename_collection, day_begin, day_end),
        # "has_sample_count": get_has_sample_count(db, staff_collection, bodyfacename_collection, day_begin, day_end), # FIXME:
        "checkin_count": await get_inout_count(db, staff_collection, bodyfacename_collection, in_begin, in_end),
        "checkout_count": await get_inout_count(db, staff_collection, bodyfacename_collection, out_begin, out_end),
        "total_count": await get_inout_count(
            db, staff_collection, bodyfacename_collection, day_begin, day_end
        ),  # BUG: this is not correct, change to begin of the day to end of the day
        "table": "",
    }

    # excel related part
    excel_bytes = b64decode(str(content.excel).encode("utf-8"))  # noqa: F841
    fill_excel_bytes = None
    if content.is_excel_uploaded():
        fill_excel_bytes = await extract_and_fill_excel(
            db, staff_collection, bodyfacename_collection, excel_bytes, day_begin, day_end
        )
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
