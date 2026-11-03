# CampusEats API — production-style image (FastAPI + Uvicorn, dependencies managed by uv)
FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:0.12.10 /uv /uvx /bin/

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Install dependencies first (cached layer), exactly as pinned in uv.lock.
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --no-dev --no-install-project --python-preference only-system

COPY . .
RUN useradd --system --uid 1001 campuseats \
    && mkdir -p /app/media \
    && chown -R campuseats /app/media
USER campuseats

EXPOSE 8000
# Apply migrations, then serve. Proxy headers are trusted because only the web container
# (SvelteKit) can reach this port inside the Compose network.
CMD ["sh", "-c", "alembic upgrade head && exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips='*'"]
