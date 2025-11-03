import os

from dotenv import load_dotenv

load_dotenv()


class Settings:
    SERVICE_NAME: str = "Saga Orchestrator"
    VERSION: str = "1.0.0"
    HOST: str = os.getenv("HOST")
    PORT: int = int(os.getenv("PORT"))

    SERVICES: dict[str, str] = {
        "catalog": os.getenv("CATALOG_URL"),
        "payments": os.getenv("PAYMENTS_URL"),
        "inventory": os.getenv("INVENTORY_URL"),
        "purchases": os.getenv("PURCHASES_URL"),
    }

    HTTP_TIMEOUT: float = float(os.getenv("HTTP_TIMEOUT"))
    NETWORK_LATENCY_SIMULATION: float = 0.1

    LOG_LEVEL: str = os.getenv("LOG_LEVEL")


settings = Settings()
