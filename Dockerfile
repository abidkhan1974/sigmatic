FROM python:3.11-slim

WORKDIR /app

COPY pyproject.toml .
COPY sigmatic/ sigmatic/
COPY migrations/ migrations/
COPY alembic.ini .

RUN pip install --no-cache-dir .

CMD ["sigmatic", "serve"]
