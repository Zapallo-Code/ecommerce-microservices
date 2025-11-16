FROM python:3.14.0-alpine3.22

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PATH="/app/.venv/bin:$PATH" \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    # Production server settings
    WORKERS=4 \
    WORKER_CLASS=uvicorn.workers.UvicornWorker \
    TIMEOUT=30 \
    GRACEFUL_TIMEOUT=10 \
    KEEPALIVE=5

WORKDIR /app/

# Install uv and dumb-init for proper signal handling
COPY --from=ghcr.io/astral-sh/uv:0.9.3 /uv /uvx /bin/
RUN apk add --no-cache dumb-init curl

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser && chown -R appuser:appuser /app

# Install dependencies (cacheable layer)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

# Copy application code
COPY --chown=appuser:appuser ./app /app/app

# Sync the project (install the project itself)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-dev

# Switch to a non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Use dumb-init to handle signals properly
ENTRYPOINT ["/usr/bin/dumb-init", "--"]

# Run with Gunicorn + Uvicorn workers for production
CMD ["/app/.venv/bin/gunicorn", "app.main:app", \
    "--bind", "0.0.0.0:8000", \
    "--workers", "4", \
    "--worker-class", "uvicorn.workers.UvicornWorker", \
    "--timeout", "30", \
    "--access-logfile", "-", \
    "--error-logfile", "-", \
    "--log-level", "info"]
