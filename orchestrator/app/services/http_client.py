import asyncio
import logging

import httpx
from fastapi import HTTPException, status

from app.config import settings

logger = logging.getLogger(__name__)


class ServiceClient:
    def __init__(self) -> None:
        self.timeout = settings.HTTP_TIMEOUT

    def _get_service_url(self, service_name: str) -> str:
        """Get service URL from settings."""
        if service_name not in settings.SERVICES:
            raise ValueError(f"Unknown service: {service_name}")
        return settings.SERVICES[service_name]

    async def _make_request(
        self,
        client: httpx.AsyncClient,
        method: str,
        url: str,
        data: dict[str, object] | None = None,
    ) -> httpx.Response:
        """Make HTTP request based on method."""
        method_map = {
            "GET": lambda: client.get(url),
            "POST": lambda: client.post(url, json=data),
            "PUT": lambda: client.put(url, json=data),
            "DELETE": lambda: client.delete(url),
        }

        if method not in method_map:
            raise ValueError(f"Unsupported HTTP method: {method}")

        return await method_map[method]()

    def _extract_error_detail(self, response: httpx.Response) -> str:
        """Extract error detail from response."""
        try:
            error_json = response.json()
            return error_json.get("error", error_json.get("message", response.text))
        except Exception:
            return response.text

    def _handle_http_error(
        self, service_name: str, error: httpx.HTTPStatusError
    ) -> None:
        """Handle HTTP status errors consistently."""
        status_code = error.response.status_code
        error_detail = self._extract_error_detail(error.response)

        logger.error(f"HTTP {status_code} error in {service_name}: {error_detail}")

        raise HTTPException(
            status_code=status_code,
            detail=f"{service_name} error: {error_detail}",
        )

    async def call_service(
        self,
        service_name: str,
        endpoint: str,
        method: str = "GET",
        data: dict[str, object] | None = None,
        timeout: float | None = None,
    ) -> dict[str, object]:
        """Call a microservice with the specified method and data."""
        url = f"{self._get_service_url(service_name)}{endpoint}"
        request_timeout = timeout or self.timeout

        try:
            await asyncio.sleep(settings.NETWORK_LATENCY_SIMULATION)

            async with httpx.AsyncClient(
                timeout=request_timeout, follow_redirects=True
            ) as client:
                response = await self._make_request(client, method, url, data)
                response.raise_for_status()
                return response.json()

        except httpx.TimeoutException:
            logger.error(f"Timeout calling {service_name}{endpoint}")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail=f"Timeout communicating with {service_name}",
            )
        except httpx.HTTPStatusError as e:
            self._handle_http_error(service_name, e)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error calling {service_name}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Service {service_name} unavailable",
            )
