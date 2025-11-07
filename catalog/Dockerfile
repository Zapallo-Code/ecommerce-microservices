FROM python:3.14.0-alpine3.22

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PATH="/app/.venv/bin:$PATH" \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    # Django settings
    DJANGO_SETTINGS_MODULE=main.settings \
    # Production server settings
    WORKERS=4 \
    WORKER_CLASS=sync \
    TIMEOUT=30 \
    GRACEFUL_TIMEOUT=10 \
    KEEPALIVE=5

WORKDIR /app/

# Install uv, dumb-init for proper signal handling, and PostgreSQL client libraries
COPY --from=ghcr.io/astral-sh/uv:0.9.3 /uv /uvx /bin/
RUN apk add --no-cache \
    dumb-init \
    curl \
    postgresql-libs \
    && apk add --no-cache --virtual .build-deps \
    gcc \
    musl-dev \
    postgresql-dev

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser && chown -R appuser:appuser /app

# Install dependencies (cacheable layer)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-install-project --no-dev

# Remove build dependencies
RUN apk del .build-deps

# Copy application code
COPY --chown=appuser:appuser ./main /app/main
COPY --chown=appuser:appuser ./products /app/products
COPY --chown=appuser:appuser ./manage.py /app/manage.py

# Sync the project (install the project itself)
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --frozen --no-dev

# Switch to a non-root user
USER appuser

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8001/api/health/ || exit 1

# Use dumb-init to handle signals properly
ENTRYPOINT ["/usr/bin/dumb-init", "--"]

# Run with Gunicorn for production
CMD ["gunicorn", "main.wsgi:application", \
    "--bind", "0.0.0.0:8001", \
    "--workers", "${WORKERS}", \
    "--worker-class", "${WORKER_CLASS}", \
    "--timeout", "${TIMEOUT}", \
    "--graceful-timeout", "${GRACEFUL_TIMEOUT}", \
    "--keepalive", "${KEEPALIVE}", \
    "--access-logfile", "-", \
    "--error-logfile", "-", \
    "--log-level", "info"]
