### Run with Docker

Start containers:

```bash
docker-compose up -d
```

Stop containers:

```bash
docker-compose down
```

### Run locally (Poetry)

Run the FastAPI app:

```bash
poetry run python -m src.main
```

Alternative (direct uvicorn):

```bash
poetry run uvicorn src.main:app --reload
```

### Migrations (Alembic)

Create a new migration:

```bash
poetry run alembic revision -m "message" --autogenerate
```

Apply migrations:

```bash
poetry run alembic upgrade head
```

### Documentation

Make docs in Windows OS

```bash
 .\\make.bat html
```

Make docs in Linux

```bash
 make html (for linux)
```

Generated docs will be in the `docs/_build/html` directory. Entry point for docs would be `docs/_build/html/index.html`.

### Tests

```bash
poetry run pytest
```

