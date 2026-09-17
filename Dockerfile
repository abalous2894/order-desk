FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY pyproject.toml README.md alembic.ini ./
COPY alembic ./alembic
COPY src ./src
COPY scripts/docker-entrypoint.sh /entrypoint.sh

RUN pip install --no-cache-dir -e . && chmod +x /entrypoint.sh

ENV DISABLE_OPENAPI=true

EXPOSE 8000

CMD ["/entrypoint.sh"]
