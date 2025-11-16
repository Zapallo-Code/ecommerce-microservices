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

            async with httpx.AsyncClient(
                timeout=timeout, follow_redirects=True
            ) as client:
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

                # Manejar explícitamente 409 Conflict
                # Este código indica fallo en el paso de la Saga
                if response.status_code == 409:
                    logger.warning(
                        f"Conflict (409) in {service_name}{endpoint}: "
                        f"Service returned conflict status"
                    )
                    error_detail = response.text
                    try:
                        error_json = response.json()
                        error_detail = error_json.get(
                            "error", error_json.get("message", response.text)
                        )
                    except Exception:
                        pass

                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"{service_name} conflict: {error_detail}",
                    )

                # Verificar otros errores HTTP
                response.raise_for_status()
                result: dict[str, object] = response.json()
                return result

        except httpx.TimeoutException:
            logger.error(f"Timeout while calling {service_name}{endpoint}")
            raise HTTPException(
                status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                detail=f"Timeout while communicating with {service_name}",
            )
        except httpx.HTTPStatusError as e:
            # Este bloque solo se ejecuta si no es 409 (ya manejado arriba)
            logger.error(f"HTTP error in {service_name}: {e.response.status_code}")
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Error in {service_name}: {e.response.text}",
            )
        except HTTPException:
            # Re-raise HTTPException para que no se capture abajo
            raise
        except Exception as e:
            logger.error(f"Unexpected error while calling {service_name}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Service {service_name} unavailable",
            )
