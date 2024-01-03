# Service for generate and send reports

## Run

Run directly

```bash
FORCE_ENV_FOR_DYNACONF="production" python -m src.mypk
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
