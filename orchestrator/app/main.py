import logging

from fastapi import FastAPI

from app.config import settings

logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

app = FastAPI(
    title=settings.SERVICE_NAME,
    version=settings.VERSION,
    description="Saga Orchestrator",
)


@app.get("/")
async def root() -> dict[str, str]:
    return {
        "service": settings.SERVICE_NAME,
        "status": "running",
        "version": settings.VERSION,
    }


@app.get("/health")
async def health_check() -> dict[str, object]:
    return {"status": "healthy", "services": settings.SERVICES}
