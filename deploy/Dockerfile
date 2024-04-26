FROM python:3.10

ENV TZ Asia/Ho_Chi_Minh
WORKDIR /usr/src/app
COPY requirements/requirements.txt ./
RUN pip install -r requirements.txt --no-cache-dir -r requirements.txt --index-url http://192.168.44.228:8081/repository/pypi-all/simple --trusted-host 192.168.44.228

COPY src src
COPY settings.toml settings.toml

CMD [ "python", "-m", "src.reportservice" ]