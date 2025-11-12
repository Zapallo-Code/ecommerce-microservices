# Health Check Endpoints - Documentación

Este documento describe los endpoints de health check implementados para el microservicio de catálogo.

## Descripción

Los health checks son esenciales para:
- Monitorear el estado del servicio
- Integración con orquestadores (Docker, Kubernetes)
- Alertas y diagnóstico de problemas
- Balanceo de carga inteligente

## Endpoints Disponibles

### 1. Health Check Básico

**Endpoint:** `GET /catalog/health/`

**Descripción:** Verificación básica de que el servicio está respondiendo.

**Respuesta Exitosa (200):**
```json
{
    "status": "ok",
    "service": "catalog",
    "timestamp": "2025-11-12T18:30:00.123456Z"
}
```

**Uso:**
```bash
curl http://localhost:8000/catalog/health/
```

**Características:**
- ✅ Respuesta rápida (sin verificaciones pesadas)
- ✅ Ideal para monitoreo básico
- ✅ Siempre retorna 200 si el servicio responde

---

### 2. Health Check Detallado

**Endpoint:** `GET /catalog/health/detailed/`

**Descripción:** Verificación completa del estado del servicio, incluyendo conectividad con la base de datos y estadísticas de productos.

**Respuesta Exitosa (200):**
```json
{
    "status": "ok",
    "service": "catalog",
    "timestamp": "2025-11-12T18:30:00.123456Z",
    "checks": {
        "database": {
            "status": "ok",
            "message": "Database connection successful"
        },
        "products": {
            "status": "ok",
            "total": 10,
            "active": 10,
            "available": 10
        }
    }
}
```

**Respuesta con Problemas (503):**
```json
{
    "status": "degraded",
    "service": "catalog",
    "timestamp": "2025-11-12T18:30:00.123456Z",
    "checks": {
        "database": {
            "status": "error",
            "message": "Database connection failed: ..."
        },
        "products": {
            "status": "error",
            "message": "Error querying products: ..."
        }
    }
}
```

**Uso:**
```bash
curl http://localhost:8000/catalog/health/detailed/
```

**Características:**
- ✅ Verifica conexión a la base de datos
- ✅ Cuenta productos totales, activos y disponibles
- ✅ Retorna 503 si hay problemas
- ✅ Útil para diagnóstico detallado

---

### 3. Readiness Check (Kubernetes)

**Endpoint:** `GET /catalog/health/ready/`

**Descripción:** Verifica si el servicio está listo para recibir tráfico. Usado por Kubernetes para determinar si el pod debe recibir requests.

**Respuesta Lista (200):**
```json
{
    "status": "ready",
    "service": "catalog",
    "timestamp": "2025-11-12T18:30:00.123456Z"
}
```

**Respuesta No Lista (503):**
```json
{
    "status": "not_ready",
    "service": "catalog",
    "timestamp": "2025-11-12T18:30:00.123456Z",
    "error": "connection to database failed"
}
```

**Uso:**
```bash
curl http://localhost:8000/catalog/health/ready/
```

**Características:**
- ✅ Verifica conectividad con dependencias críticas
- ✅ Valida que se pueden hacer consultas a la BD
- ✅ Retorna 503 si no está listo para tráfico
- ✅ Usado por Kubernetes readiness probes

---

### 4. Liveness Check (Kubernetes)

**Endpoint:** `GET /catalog/health/live/`

**Descripción:** Verifica si el servicio está vivo y respondiendo. Usado por Kubernetes para detectar si el pod necesita ser reiniciado.

**Respuesta (200):**
```json
{
    "status": "alive",
    "service": "catalog",
    "timestamp": "2025-11-12T18:30:00.123456Z"
}
```

**Uso:**
```bash
curl http://localhost:8000/catalog/health/live/
```

**Características:**
- ✅ Verificación ligera (solo responde)
- ✅ No verifica dependencias externas
- ✅ Siempre retorna 200 si el servicio responde
- ✅ Usado por Kubernetes liveness probes

---

## Integración con Docker

### Dockerfile con Health Check

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# ... instalación de dependencias ...

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=40s --retries=3 \
  CMD curl -f http://localhost:8000/catalog/health/ || exit 1

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

---

## Integración con Kubernetes

### Deployment con Probes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: catalog-service
spec:
  replicas: 3
  template:
    spec:
      containers:
      - name: catalog
        image: catalog-service:latest
        ports:
        - containerPort: 8000
        
        # Liveness probe - Reinicia el pod si falla
        livenessProbe:
          httpGet:
            path: /catalog/health/live/
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
          timeoutSeconds: 5
          failureThreshold: 3
        
        # Readiness probe - Quita el pod del balanceador si falla
        readinessProbe:
          httpGet:
            path: /catalog/health/ready/
            port: 8000
          initialDelaySeconds: 15
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 2
```

---

## Integración con Docker Compose

### docker-compose.yml

```yaml
version: '3.8'

services:
  catalog:
    build: ./catalog
    ports:
      - "8000:8000"
    environment:
      - DATABASE_HOST=db
      - DATABASE_PORT=5432
    depends_on:
      - db
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/catalog/health/"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    
  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=ms_catalog
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5
```

---

## Monitoreo con Scripts

### Script de Monitoreo Bash

```bash
#!/bin/bash

# monitor_catalog.sh
ENDPOINT="http://localhost:8000/catalog/health/detailed/"
INTERVAL=30

while true; do
    RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $ENDPOINT)
    TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
    
    if [ $RESPONSE -eq 200 ]; then
        echo "[$TIMESTAMP] ✅ Catalog service is healthy (HTTP $RESPONSE)"
    else
        echo "[$TIMESTAMP] ❌ Catalog service is unhealthy (HTTP $RESPONSE)"
        # Enviar alerta
        # send_alert "Catalog service is down"
    fi
    
    sleep $INTERVAL
done
```

### Script de Monitoreo Python

```python
import requests
import time
from datetime import datetime

def check_health():
    url = "http://localhost:8000/catalog/health/detailed/"
    
    try:
        response = requests.get(url, timeout=5)
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        if response.status_code == 200:
            data = response.json()
            print(f"[{timestamp}] ✅ Service: {data['status']}")
            print(f"  - Database: {data['checks']['database']['status']}")
            print(f"  - Products: {data['checks']['products']['total']} total")
        else:
            print(f"[{timestamp}] ❌ Service unhealthy (HTTP {response.status_code})")
    except Exception as e:
        print(f"[{timestamp}] ❌ Error checking health: {e}")

if __name__ == "__main__":
    while True:
        check_health()
        time.sleep(30)
```

---

## Testing

### Prueba Manual con curl

```bash
# Test básico
curl -i http://localhost:8000/catalog/health/

# Test detallado
curl -i http://localhost:8000/catalog/health/detailed/ | jq

# Test readiness
curl -i http://localhost:8000/catalog/health/ready/

# Test liveness
curl -i http://localhost:8000/catalog/health/live/
```

### Prueba Automatizada con pytest

```python
import pytest
import requests

BASE_URL = "http://localhost:8000"

def test_basic_health_check():
    """Test que el health check básico responde correctamente"""
    response = requests.get(f"{BASE_URL}/catalog/health/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "catalog"
    assert "timestamp" in data

def test_detailed_health_check():
    """Test que el health check detallado incluye información de checks"""
    response = requests.get(f"{BASE_URL}/catalog/health/detailed/")
    assert response.status_code in [200, 503]
    data = response.json()
    assert "checks" in data
    assert "database" in data["checks"]
    assert "products" in data["checks"]

def test_readiness_check():
    """Test que el readiness check responde"""
    response = requests.get(f"{BASE_URL}/catalog/health/ready/")
    assert response.status_code in [200, 503]
    data = response.json()
    assert data["service"] == "catalog"

def test_liveness_check():
    """Test que el liveness check siempre responde OK"""
    response = requests.get(f"{BASE_URL}/catalog/health/live/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "alive"
```

---

## Resumen de Endpoints

| Endpoint | Propósito | Retorna 503 | Uso Principal |
|----------|-----------|-------------|---------------|
| `/catalog/health/` | Health check básico | No | Monitoreo simple |
| `/catalog/health/detailed/` | Health check completo | Sí | Diagnóstico |
| `/catalog/health/ready/` | Readiness probe | Sí | Kubernetes |
| `/catalog/health/live/` | Liveness probe | No | Kubernetes |

---

## Mejores Prácticas

1. **Usar `/live/` para liveness probes** - No verifica dependencias externas
2. **Usar `/ready/` para readiness probes** - Verifica que el servicio está listo para tráfico
3. **Usar `/detailed/` para debugging** - Proporciona información completa
4. **Configurar timeouts apropiados** - 3-5 segundos es suficiente
5. **Monitorear métricas de health checks** - Tasa de fallos, latencia, etc.
