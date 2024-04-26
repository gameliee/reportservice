# Service for generate and send reports

[![Build Status](http://192.168.44.233:8080/buildStatus/icon?job=STFace_reportservice&build=last)](http://192.168.44.233:8080/job/STFace_reportservice/lastBuild/) [![Coverage](http://192.168.44.233:8080/buildStatus/icon?job=STFace_reportservice&subject=Coverage&color=${colorLineCoverage}&status=${lineCoverage})](http://192.168.44.233:8080/job/STFace_reportservice/lastBuild/coverage/) ![Image](http://192.168.44.233:8080/buildStatus/icon?job=STFace_reportservice&config=dockerbuild)

## Run

Run directly

```bash
ENV_FOR_DYNACONF="production" python -m src.reportservice
```

Or use the docker deployment

```bash
cd deploy
docker compose up -d
```

## Test

```bash
pytest --cov --cov-report term-missing
```
