import pytest


@pytest.fixture(scope="session")
def temp_log_file(tmpdir_factory):
    return str(tmpdir_factory.mktemp("log")) + "/aaa/debug.log"
