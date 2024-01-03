import os
import pytest


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
def dbsetup(request):
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

    # TODO: Override database settings settings.DB_URL, settings.DB_NAME
    mongo = f"mongodb://dat:password@{docker_ip}:{dbport}/general?authSource=admin&retryWrites=true&w=majority"
    return mongo
