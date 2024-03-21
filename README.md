# Service for generate and send reports

[![Build Status](http://172.23.111.200:8080/buildStatus/icon?job=reportservice2&build=last)](http://172.23.111.200:8080/job/reportservice2/)

![Coverage](http://172.23.111.200:8080/buildStatus/icon?job=reportservice2&subject=Coverage&color=${colorInstructionCoverage}&status=${instructionCoverage})

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
