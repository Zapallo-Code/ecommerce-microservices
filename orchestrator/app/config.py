import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    SERVICE_NAME: str = "Saga Orchestrator"
    VERSION: str = "1.0.0"
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    SERVICES: dict[str, str] = {
        "catalog": os.getenv("CATALOG_URL", "http://localhost:8001"),
        "payments": os.getenv("PAYMENTS_URL", "http://localhost:8002"),
        "inventory": os.getenv("INVENTORY_URL", "http://localhost:8003"),
        "purchases": os.getenv("PURCHASES_URL", "http://localhost:8004"),
    }

    HTTP_TIMEOUT: float = float(os.getenv("HTTP_TIMEOUT", "30.0"))
    NETWORK_LATENCY_SIMULATION: float = 0.1

    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


settings = Settings()
