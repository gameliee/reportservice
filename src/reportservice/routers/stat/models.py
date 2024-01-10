"""data models"""
from typing import Annotated

StaffCodeStr = Annotated[str, "staff code"]


class DFConst:
    # QUERY_TIMEOUT = 10
    # TITLE = "title"
    # DEPARTMENT = "department"
    # UNIT = "unit"
    # STAFFCODE = "staffcode"
    # EMAIL = "email"
    # FULLNAME = "fullname"
    # CHECKIN = "checkin"
    # CHECKOUT = "checkout"

    # excel columns
    STAFF = "mã nhân viên"
    FIRST = "ghi nhận lần đầu"
    LASTT = "ghi nhận lần cuối"
    SAMPL = "trạng thái mẫu"


class QueryException(Exception):
    pass
