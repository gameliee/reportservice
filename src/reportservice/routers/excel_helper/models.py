"""data models"""
from typing import Annotated

StaffCodeStr = Annotated[str, "staff code"]


class AppConst:
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
    ESTAFF = "mã nhân viên"
    EFIRST = "ghi nhận lần đầu"
    ELASTT = "ghi nhận lần cuối"
    ESAMPL = "trạng thái mẫu"


class ExcelInvalidException(Exception):
    pass
