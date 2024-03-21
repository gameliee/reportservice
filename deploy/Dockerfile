FROM python:3.10

ENV TZ Asia/Ho_Chi_Minh
WORKDIR /usr/src/app
COPY requirements/requirements.txt ./
RUN pip install -r requirements.txt --no-cache-dir -r requirements.txt --index-url http://172.23.111.200:8081/repository/pypi-all/simple --trusted-host 172.23.111.200

COPY src src
COPY settings.toml settings.toml

CMD [ "python", "-m", "src.reportservice" ]