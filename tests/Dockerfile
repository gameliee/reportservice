FROM dat.local:5001/docker.io/library/python:3.10 as runtime

ENV TZ Asia/Ho_Chi_Minh
WORKDIR /usr/src/app

COPY requirements/requirements.txt ./
RUN pip install -r requirements.txt --no-cache-dir --index-url http://192.168.44.228:8081/repository/pypi-all/simple --trusted-host 192.168.44.228
COPY src src
COPY settings.toml settings.toml

FROM runtime as test
COPY requirements/dev-requirements.txt ./
RUN pip install -r dev-requirements.txt --no-cache-dir --index-url http://192.168.44.228:8081/repository/pypi-all/simple --trusted-host 192.168.44.228

COPY tests/test.xlsx tests/test.xlsx
COPY tests/invalid.xlsx tests/invalid.xlsx
COPY conftest.py conftest.py

CMD [ "pytest --docker" ]