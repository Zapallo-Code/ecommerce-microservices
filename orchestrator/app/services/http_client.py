import asyncio
import logging

import httpx
from fastapi import HTTPException, status

from app.config import settings

logger = logging.getLogger(__name__)


class ServiceClient:
    @staticmethod
    async def call_service(
        service_name: str,
        endpoint: str,
        method: str = "GET",
        data: dict[str, object] | None = None,
        timeout: float | None = None,
    ) -> dict[str, object]:
        if service_name not in settings.SERVICES:
            raise ValueError(f"Unknown service: {service_name}")

        url = f"{settings.SERVICES[service_name]}{endpoint}"
        timeout = timeout or settings.HTTP_TIMEOUT

        try:
            await asyncio.sleep(settings.NETWORK_LATENCY_SIMULATION)

            async with httpx.AsyncClient(timeout=timeout) as client:
                if method == "GET":
                    response = await client.get(url)
                elif method == "POST":
                    response = await client.post(url, json=data)
                elif method == "PUT":
                    response = await client.put(url, json=data)
                elif method == "DELETE":
                    response = await client.delete(url)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                response.raise_for_status()
                return response.json()

        except httpx.TimeoutException:
            logger.error(f"Timeout while calling {service_name}{endpoint}")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail=f"Timeout while communicating with {service_name}",
            )
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error in {service_name}: {e.response.status_code}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Error in {service_name}: {e.response.text}",
            )
        except Exception as e:
            logger.error(f"Unexpected error while calling {service_name}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Service {service_name} unavailable",
            )
