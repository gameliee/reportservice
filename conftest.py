import os
import random
import string
import pytest
import uuid
from datetime import datetime


@pytest.fixture(scope="session")
def temp_log_file(tmpdir_factory):
    return str(tmpdir_factory.mktemp("log")) + "/aaa/debug.log"


@pytest.fixture(scope="session")
def docker_compose_file(pytestconfig):
    return (os.path.join(str(pytestconfig.rootdir), "tests", "docker-compose-mongo.yml"),)


@pytest.fixture(scope="session")
def docker_compose_project_name(pytestconfig):
    """Generate a project name using the projects root directory.

    Override this fixture in your tests if you need a particular project name.
    """
    return "test_reportservice"


def pytest_addoption(parser):
    parser.addoption("--createdb", action="store_true", help="Enable the dbsetup fixture")


@pytest.fixture(scope="session", autouse=True)
def dburi(request):
    """ensure postgres db and central is up"""

    # if run test without `--createdb`, do not start up the mongo docker
    if not request.config.getoption("--createdb"):
        return "mongodb://foo:password@localhost:27017/general?authSource=admin&retryWrites=true&w=majority"

    docker_ip = request.getfixturevalue("docker_ip")
    docker_services = request.getfixturevalue("docker_services")

    from pymongo import MongoClient

    def is_responsive(docker_ip, port):
        try:
            MongoClient(host=docker_ip, port=port, serverSelectionTimeoutMS=5000).admin.command("ismaster"),
        except Exception:
            return False
        return True

    # `port_for` takes a container port and returns the corresponding host port
    dbport = docker_services.port_for("mongo", 27017)
    docker_services.wait_until_responsive(timeout=30.0, pause=0.1, check=lambda: is_responsive(docker_ip, dbport))

    mongo = f"mongodb://foo:password@{docker_ip}:{dbport}/general?authSource=admin&retryWrites=true&w=majority"
    return mongo


@pytest.fixture(scope="session")
def collectionconfig(request):
    return {
        "staff_collection": "staffs",
        "face_collection": "BodyFaceName",
    }


@pytest.fixture(scope="session")
def smtpconfig(request):
    """A example email settings that actually works"""
    if request.config.getoption("--createdb"):
        return {
            "enable": "true",
            "account": "testnv@example.com",
            "password": "anypassword",
            "port": 25,
            "server": "smtp",
            "username": "testuser",
            "useSSL": False,
        }
    else:
        return {
            "enable": "true",
            "account": "testnv@example.com",
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
    return path


@pytest.fixture(scope="session")
def excelbytes(excelfile):
    """Bytes of a example excel file"""
    with open(excelfile, "rb") as f:
        yield f.read()


@pytest.fixture(scope="session")
def random_collection_name(dburi):
    collection_name = "".join(random.choices(string.ascii_lowercase, k=10))
    return collection_name


@pytest.fixture
def renderdate():
    """only date part is interested"""
    return datetime.fromisoformat("2023-12-27T00:00:00.000+00:00")


@pytest.fixture
def test_time(renderdate: datetime):
    day_begin = datetime.combine(date=renderdate.date(), time=datetime.min.time())
    day_end = datetime.combine(date=renderdate.date(), time=datetime.max.time())
    return day_begin, day_end


@pytest.fixture(scope="session")
def testcontentid(testclient) -> str:
    testid = "test_" + str(uuid.uuid1())
    yield testid


@pytest.fixture(scope="session")
def invalidexcelfile(pytestconfig):
    path = os.path.join(str(pytestconfig.rootdir), "tests", "invalid.xlsx")
    return path


@pytest.fixture(scope="session")
def invalidexcelbytes(invalidexcelfile):
    with open(invalidexcelfile, "rb") as f:
        yield f.read()


@pytest.fixture(scope="session")
def testtaskid(testclient) -> str:  # noqa: F811
    testid = "test_" + str(uuid.uuid1())
    yield testid
