FROM python:3.14.0-alpine3.22

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PATH="/app/.venv/bin:$PATH" \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app/

# Install uv
COPY --from=ghcr.io/astral-sh/uv:0.9.3 /uv /uvx /bin/

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser && chown -R appuser:appuser /app

# Install dependencies (cacheable layer)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

# Copy application code
COPY ./app /app/app

# Sync the project (install the project itself)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-dev

# Switch to a non-root user
USER appuser

CMD ["fastapi", "run", "--workers", "4", "app/main.py"]
