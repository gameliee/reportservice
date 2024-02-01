# Service for generate and send reports

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
