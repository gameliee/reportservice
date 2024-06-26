import os
import pytest
from datetime import datetime


@pytest.fixture(scope="session")
def temp_log_file(tmpdir_factory):
    return str(tmpdir_factory.mktemp("log")) + "/aaa/debug.log"


def pytest_addoption(parser):
    parser.addoption("--docker", action="store_true", help="use the network inside docker-compose")


@pytest.fixture(scope="session")
def admindburi():
    default_admin_uri = "mongodb://foo:password@localhost:27017/general?authSource=admin&retryWrites=true&w=majority"
    admindburi = os.environ.get("DB_ADMIN_URL_FOR_TEST", default_admin_uri)
    assert admindburi is not None
    return admindburi
    # """ensure postgres db and central is up"""
    # if request.config.getoption("--docker"):
    #     return "mongodb://root:password@mongodb:27017/general?authSource=admin&retryWrites=true&w=majority"
    # else:
    #     return "mongodb://foo:password@localhost:27017/general?authSource=admin&retryWrites=true&w=majority"


@pytest.fixture(scope="session")
def avai_staff():
    return ["219085", "206424", "267817"]


@pytest.fixture(scope="session")
def collectionconfig(request):
    return {
        "database": "FaceID",
        "staff_collection": "staffs",
        "face_collection": "BodyFaceName",
    }


@pytest.fixture(scope="session")
def smtpconfig(request):
    """A example email settings that actually works"""
    if request.config.getoption("--docker"):
        return {
            "enable": "true",
            "account": "pytest@insidedocker.com",
            "password": "anypassword",
            "port": 25,
            "server": "smtp",
            "username": "testuser_inside_docker",
            "useSSL": False,
        }
    else:
        return {
            "enable": "true",
            "account": "pytest@example.com",
            "password": "anypassword",
            "port": 1026,
            "server": "localhost",
            "username": "testuser",
            "useSSL": False,
        }


@pytest.fixture(scope="session")
def excelfile(pytestconfig):
    """Path to a example excel file"""
    path = os.path.join(str(pytestconfig.rootdir), "tests", "test.xlsx")
    assert os.path.exists(path)
    return path


@pytest.fixture(scope="session")
def excelbytes(excelfile):
    """Bytes of a example excel file"""
    with open(excelfile, "rb") as f:
        yield f.read()


@pytest.fixture(scope="session")
def random_database_name():
    """do not use random database name for this test, cause users have rules"""
    return "TestReportService"


@pytest.fixture(scope="session")
def renderdate():
    """only date part is interested"""
    return datetime.fromisoformat("2023-12-27T00:00:00.000+00:00")


@pytest.fixture(scope="session")
def test_time(renderdate: datetime):
    day_begin = datetime.combine(date=renderdate.date(), time=datetime.min.time(), tzinfo=renderdate.tzinfo)
    day_end = datetime.combine(date=renderdate.date(), time=datetime.max.time(), tzinfo=renderdate.tzinfo)
    return day_begin, day_end


@pytest.fixture(scope="session")
def invalidexcelfile(pytestconfig):
    path = os.path.join(str(pytestconfig.rootdir), "tests", "invalid.xlsx")
    assert os.path.exists(path)
    return path


@pytest.fixture(scope="session")
def invalidexcelbytes(invalidexcelfile):
    with open(invalidexcelfile, "rb") as f:
        yield f.read()
