# E-Commerce Microservices - Saga Pattern

Sistema de e-commerce distribuido implementando el patrón **Saga con Orquestación** para manejo de transacciones distribuidas.

## 📋 Tabla de Contenidos

- [Arquitectura del Sistema](#-arquitectura-del-sistema)
- [Tecnologías Utilizadas](#-tecnologías-utilizadas)
- [Microservicios](#-microservicios)
- [Traefik - Reverse Proxy](#-traefik---reverse-proxy)
- [Patrón Saga](#-patrón-saga)
- [Requisitos Previos](#-requisitos-previos)
- [Instalación](#-instalación)
- [Configuración](#-configuración)
- [Ejecución](#-ejecución)
- [API Endpoints](#-api-endpoints)
- [Testing](#-testing)
- [Troubleshooting](#-troubleshooting)

---

## 🏗 Arquitectura del Sistema

El sistema está compuesto por **5 microservicios** independientes que se comunican a través de HTTP REST APIs mediante **Traefik** como Reverse Proxy, coordinados por un **orquestador Saga**:

```
                         ┌─────────────────────────────────────┐
                         │            TRAEFIK                  │
                         │        Reverse Proxy                │
                         │         Puerto: 80                  │
                         │      Dashboard: 8080                │
                         └───────────────┬─────────────────────┘
                                         │
        ┌────────────────────────────────┼────────────────────────────────┐
        │                                │                                │
        ▼                                ▼                                ▼
   /api/catalog                    /api/saga                       /api/payments
        │                                │                                │
        ▼                                ▼                                ▼
┌──────────────┐            ┌────────────────────┐            ┌──────────────┐
│   CATALOG    │            │    ORCHESTRATOR    │            │   PAYMENTS   │
│   (Django)   │            │     (FastAPI)      │            │   (Django)   │
│  Puerto:8001 │            │    Puerto: 8000    │            │  Puerto:8002 │
│              │            │                    │            │              │
│ • Productos  │            │ • Coordina Saga    │            │ • Pagos      │
│ • Siempre OK │            │ • Compensaciones   │            │ • Reembolsos │
└──────────────┘            └────────────────────┘            │ • 5% fallo   │
                                                              └──────────────┘
        ┌────────────────────────────────┼────────────────────────────────┐
        │                                                                 │
        ▼                                                                 ▼
   /api/inventory                                                  /api/purchases
        │                                                                 │
        ▼                                                                 ▼
┌──────────────┐                                                  ┌──────────────┐
│  INVENTORY   │                                                  │  PURCHASES   │
│   (Django)   │                                                  │   (Django)   │
│  Puerto:8003 │                                                  │  Puerto:8004 │
│              │                                                  │              │
│ • Stock      │                                                  │ • Compras    │
│ • 30% fallo  │                                                  │ • Cancela.   │
│ • Compensar  │                                                  │ • 5% fallo   │
└──────────────┘                                                  └──────────────┘
        │                                                                 │
        └─────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
                    ┌──────────────────────────────┐
                    │       PostgreSQL             │
                    │                              │
                    │  • ms_catalog   (Productos)  │
                    │  • ms_payments  (Pagos)      │
                    │  • ms_inventory (Inventario) │
                    │  • ms_purchases (Compras)    │
                    └──────────────────────────────┘
```

### Flujo de una Transacción Saga

```
1. Cliente → POST /api/saga/transaction → Traefik → Orchestrator
2. Orchestrator → GET /api/catalog/products/random/ → Traefik → Catalog (siempre éxito)
3. Orchestrator → POST /api/payments/payments/ → Traefik → Payments (5% fallo)
4. Si Payment OK → POST /api/inventory/inventory/decrease/ → Traefik → Inventory (30% fallo)
5. Si Inventory OK → POST /api/purchases/purchases/ → Traefik → Purchases (5% fallo)
6. Si todo OK → TRANSACTION COMPLETED ✅

En caso de fallo en cualquier paso:
- COMPENSACIÓN: Orchestrator ejecuta rollback en orden reverso:
  1. DELETE /api/purchases/purchases/{id}/cancel/ (si se creó)
  2. POST /api/inventory/inventory/compensate/ (si se decrementó)
  3. POST /api/payments/payments/{id}/refund/ (si se creó)
```

---

## 🛠 Tecnologías Utilizadas

### Backend

- **Python 3.14** - Lenguaje de programación
- **Django 5.2** - Framework web para catalog, payments, inventory, purchases
- **Django REST Framework 3.15** - API REST para microservicios Django
- **FastAPI 0.115** - Framework asíncrono para orchestrator
- **Pydantic** - Validación de datos en FastAPI

### Base de Datos

- **PostgreSQL 17** - Base de datos relacional
- **psycopg2** - Adaptador PostgreSQL para Python

### Infraestructura

- **Docker 24+** - Contenedorización
- **Docker Compose** - Orquestación de contenedores
- **Traefik v3** - Reverse Proxy y Load Balancer
- **uv** - Gestor de paquetes Python (ultra-rápido)
- **Gunicorn** - WSGI server para Django
- **Uvicorn** - ASGI server para FastAPI

### Herramientas de Desarrollo

- **Ruff** - Linter y formatter Python
- **pytest** - Framework de testing
- **httpx** - Cliente HTTP asíncrono

---

## 📦 Microservicios

### 1. Orchestrator (Puerto 8000)

**Tecnología:** FastAPI  
**Responsabilidad:** Coordinar transacciones distribuidas mediante Saga Pattern

#### Características:

- Orquesta el flujo completo de transacciones
- Implementa lógica de compensación (rollback)
- Mantiene estado de todas las transacciones en memoria
- No tiene base de datos propia (stateless por diseño)

#### Endpoints:

- `POST /saga/transaction` - Iniciar transacción distribuida
- `GET /saga/status/{transaction_id}` - Consultar estado de transacción
- `GET /saga/transactions` - Listar todas las transacciones

#### Estructura del Proyecto:

```
orchestrator/
├── app/
│   ├── config.py              # Configuración (URLs de servicios)
│   ├── main.py                # FastAPI app
│   ├── models.py              # Modelos Pydantic
│   ├── routes/
│   │   └── saga_routes.py     # Endpoints REST
│   ├── services/
│   │   ├── compensation.py    # Lógica de compensación
│   │   ├── http_client.py     # Cliente HTTP para servicios
│   │   └── saga_service.py    # Lógica principal del Saga
│   └── storage/
│       └── transaction_store.py # Almacenamiento en memoria
├── Dockerfile
└── pyproject.toml
```

#### Configuración (config.py):

```python
# Los servicios se comunican a través de Traefik
CATALOG_URL = "http://traefik/api/catalog"
PAYMENTS_URL = "http://traefik/api/payments"
INVENTORY_URL = "http://traefik/api/inventory"
PURCHASES_URL = "http://traefik/api/purchases"
```

---

### 2. Catalog (Puerto 8001)

**Tecnología:** Django + Django REST Framework  
**Responsabilidad:** Proveer productos aleatorios para el Saga

#### Características:

- **Siempre retorna 200 OK** (no falla nunca)
- Genera productos aleatorios si no existen en DB
- Simula latencia de 0.1 a 0.5 segundos
- **NO requiere compensación** (solo lectura)

#### Endpoints:

- `GET /api/catalog/health/` - Health check
- `GET /api/catalog/products/random/` - Obtener producto aleatorio (siempre éxito)

#### Modelo de Datos:

```python
class Product(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    category = models.CharField(max_length=100)
    stock = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

#### Ejemplo de Respuesta:

```json
{
  "product_id": 1,
  "name": "Product-9377",
  "description": "Random product description 35",
  "price": "491.80",
  "category": "Electronics",
  "stock": 76
}
```

#### Base de Datos:

- **Nombre:** `ms_catalog`
- **Tabla:** `products`

---

### 3. Payments (Puerto 8002)

**Tecnología:** Django + Django REST Framework  
**Responsabilidad:** Procesar pagos y manejar reembolsos

#### Características:

- **5% de probabilidad de fallo aleatorio** en creación de pagos
- Retorna 200 (éxito) o 409 (conflicto/error)
- Implementa endpoint de compensación (refund)
- Simula latencia de 0.5 a 2 segundos

#### Endpoints:

- `GET /api/payments/payments/health/` - Health check
- `POST /api/payments/payments/` - Crear pago (5% fallo aleatorio)
- `POST /api/payments/payments/{id}/refund/` - Reembolsar pago (compensación)

#### Modelo de Datos:

```python
class Payment(models.Model):
    user_id = models.CharField(max_length=100)
    transaction_id = models.CharField(max_length=100)
    product_id = models.CharField(max_length=100, null=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20)  # success, error, compensated
    created_at = models.DateTimeField(auto_now_add=True)
    compensated_at = models.DateTimeField(null=True, blank=True)
```

#### Request Body (POST /payments/):

```json
{
  "user_id": "user-123",
  "transaction_id": "txn-456",
  "amount": 99.99
}
```

#### Respuesta Exitosa (200):

```json
{
  "payment_id": 42,
  "status": "success",
  "message": "Payment processed successfully",
  "transaction_id": "txn-456",
  "user_id": "user-123",
  "product_id": null
}
```

#### Respuesta de Error (409):

```json
{
  "payment_id": 43,
  "status": "error",
  "message": "Error processing payment",
  "transaction_id": "txn-457",
  "user_id": "user-123",
  "product_id": null
}
```

#### Base de Datos:

- **Nombre:** `ms_payments`
- **Tabla:** `app_payment`

---

### 4. Inventory (Puerto 8003)

**Tecnología:** Django + Django REST Framework  
**Responsabilidad:** Gestionar inventario y decrementar stock

#### Características:

- **30% de probabilidad de fallo aleatorio** (simula falta de stock)
- Retorna 200 (éxito) o 409 (stock insuficiente)
- Implementa endpoint de compensación para restaurar stock
- Simula latencia de 0.1 a 0.8 segundos

#### Endpoints:

- `GET /api/inventory/health/` - Health check
- `POST /api/inventory/inventory/decrease/` - Decrementar inventario (30% fallo)
- `POST /api/inventory/inventory/compensate/` - Restaurar inventario (compensación)

#### Modelo de Datos:

```python
class Inventory(models.Model):
    product_id = models.CharField(max_length=100, unique=True)
    quantity = models.IntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

#### Request Body (POST /inventory/decrease/):

```json
{
  "product_id": "1",
  "quantity": 2,
  "transaction_id": "txn-456"
}
```

#### Respuesta Exitosa (200):

```json
{
  "status": "success",
  "message": "Inventory decreased successfully",
  "product_id": "1",
  "remaining_quantity": 98
}
```

#### Respuesta de Error (409):

```json
{
  "status": "error",
  "message": "Insufficient stock for product 1 (random failure)"
}
```

#### Base de Datos:

- **Nombre:** `ms_inventory`
- **Tablas:** `inventory_inventory`, `inventory_inventoryoperation`

---

### 5. Purchases (Puerto 8004)

**Tecnología:** Django + Django REST Framework  
**Responsabilidad:** Registrar compras y manejar cancelaciones

#### Características:

- **5% de probabilidad de fallo aleatorio** en creación
- Retorna 201 (éxito) o 409 (conflicto)
- Implementa endpoint de compensación (cancel)
- Simula latencia de 0.05 a 0.2 segundos

#### Endpoints:

- `GET /api/purchases/health/` - Health check
- `POST /api/purchases/purchases/` - Crear compra (5% fallo aleatorio)
- `DELETE /api/purchases/purchases/{transaction_id}/cancel/` - Cancelar compra (compensación)

#### Modelo de Datos:

```python
class Purchase(models.Model):
    user_id = models.CharField(max_length=100)
    transaction_id = models.CharField(max_length=100)
    product_id = models.CharField(max_length=100)
    payment_id = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20)  # success, cancelled
    created_at = models.DateTimeField(auto_now_add=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
```

#### Request Body (POST /purchases/):

```json
{
  "user_id": "user-123",
  "transaction_id": "txn-456",
  "product_id": "1",
  "payment_id": "42",
  "amount": 99.99
}
```

#### Respuesta Exitosa (200):

```json
{
  "purchase_id": 15,
  "status": "success",
  "user_id": "user-123",
  "transaction_id": "txn-456",
  "product_id": "1",
  "payment_id": "42",
  "amount": "99.99"
}
```

#### Respuesta de Error (409):

```json
{
  "status": "error",
  "message": "Purchase failed",
  "error": "CONFLICT"
}
```

#### Base de Datos:

- **Nombre:** `ms_purchases`
- **Tabla:** `app_purchase`

---

## 🔀 Traefik - Reverse Proxy

### ¿Qué es Traefik?

**Traefik** es un reverse proxy y load balancer moderno diseñado específicamente para microservicios. En este proyecto, Traefik actúa como puerta de entrada única que enruta las peticiones a los microservicios correspondientes.

### Configuración en el Proyecto

Traefik se despliega de forma externa y los servicios se conectan a la red `traefik-public`. El puerto **80** es el punto de entrada único al sistema.

#### Características

- ✅ **Auto-descubrimiento**: Detecta automáticamente los contenedores Docker
- ✅ **Routing dinámico**: Enruta peticiones según etiquetas Docker
- ✅ **Strip Prefix**: Elimina el prefijo `/api/service` antes de enviar al servicio
- ✅ **Health checks**: Monitorea la salud de los servicios
- ✅ **Dashboard**: Interfaz web para visualizar rutas y servicios (puerto 8080)
- ✅ **HTTPS/TLS**: Soporte para certificados SSL (configurable)

### Arquitectura con Traefik

```
                    Internet/Cliente
                            │
                            ▼
                    ┌───────────────┐
                    │   TRAEFIK     │
                    │   Puerto: 80  │
                    │  (Dashboard:  │
                    │    8080)      │
                    └───────┬───────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
   /api/catalog        /api/saga          /api/payments
        │                   │                   │
        ▼                   ▼                   ▼
   catalog:8001     orchestrator:8000    payments:8002

        ▼                   ▼
   /api/inventory    /api/purchases
        │                   │
        ▼                   ▼
   inventory:8003    purchases:8004
```

### Reglas de Enrutamiento

Traefik enruta las peticiones según el path y elimina el prefijo antes de enviar al servicio:

| Path Original                       | Se transforma en          | Servicio     |
| ----------------------------------- | ------------------------- | ------------ |
| `http://localhost/api/saga/*`       | `/saga/*`                 | Orchestrator |
| `http://localhost/api/catalog/*`    | `/*`                      | Catalog      |
| `http://localhost/api/payments/*`   | `/*`                      | Payments     |
| `http://localhost/api/inventory/*`  | `/*`                      | Inventory    |
| `http://localhost/api/purchases/*`  | `/*`                      | Purchases    |

### Etiquetas Docker (Labels)

Cada servicio tiene etiquetas que Traefik lee para configurar el enrutamiento:

```yaml
# Ejemplo: Catalog
labels:
  - "traefik.enable=true"
  - "traefik.docker.network=traefik-public"
  - "traefik.http.routers.catalog.rule=PathPrefix(`/api/catalog`)"
  - "traefik.http.routers.catalog.entrypoints=web"
  - "traefik.http.services.catalog.loadbalancer.server.port=8001"
  - "traefik.http.middlewares.catalog-strip.stripprefix.prefixes=/api/catalog"
  - "traefik.http.routers.catalog.middlewares=catalog-strip"
```

**Explicación:**

- `traefik.enable=true` - Habilita Traefik para este servicio
- `traefik.docker.network=traefik-public` - Red Docker a usar
- `PathPrefix(/api/catalog)` - Coincide con URLs que empiezan con /api/catalog
- `stripprefix.prefixes=/api/catalog` - Elimina el prefijo antes de enviar al servicio
- `loadbalancer.server.port` - Puerto interno del servicio

### Dashboard de Traefik

Accede al dashboard en: **http://localhost:8080**

El dashboard muestra:

- ✅ Servicios activos y su estado
- ✅ Routers configurados
- ✅ Middlewares aplicados
- ✅ Health checks en tiempo real

### Ejemplos de Uso con Traefik

#### Probar transacción (endpoint principal):

```powershell
# PowerShell
Invoke-RestMethod -Uri "http://localhost/api/saga/transaction" -Method POST -ContentType "application/json" -Body '{"user_id": "1", "amount": 100}'
```

```bash
# Bash/curl
curl -X POST http://localhost/api/saga/transaction \
  -H "Content-Type: application/json" \
  -d '{"user_id": "1", "amount": 100}'
```

#### Verificar health de servicios:

```bash
# Health del saga
curl http://localhost/api/saga/

# Health de catalog
curl http://localhost/api/catalog/health/

# Health de payments
curl http://localhost/api/payments/payments/health/

# Health de inventory
curl http://localhost/api/inventory/health/

# Health de purchases
curl http://localhost/api/purchases/health/
```

### Ventajas de Usar Traefik

1. **Punto de Entrada Único**: Un solo puerto (80) para todos los servicios
2. **Simplicidad**: No necesitas recordar múltiples puertos
3. **Producción-Ready**: Listo para añadir HTTPS con Let's Encrypt
4. **Load Balancing**: Puede distribuir carga entre múltiples instancias
5. **Service Discovery**: Descubre servicios automáticamente
6. **Observabilidad**: Dashboard para monitoreo en tiempo real

### Configuración de Producción

Para habilitar HTTPS en producción, agrega estas etiquetas:

```yaml
labels:
  - "traefik.http.routers.orchestrator.tls=true"
  - "traefik.http.routers.orchestrator.tls.certresolver=letsencrypt"
```

Y configura el cert resolver en el servicio de Traefik:

```yaml
command:
  - "--certificatesresolvers.letsencrypt.acme.email=tu-email@ejemplo.com"
  - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
  - "--certificatesresolvers.letsencrypt.acme.tlschallenge=true"
```

### Health Checks con Traefik

Traefik monitorea automáticamente la salud de cada servicio usando los health checks definidos en Docker Compose:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8001/health/"]
  interval: 10s
  timeout: 5s
  retries: 3
  start_period: 30s
```

Si un servicio falla el health check, Traefik automáticamente deja de enviarle tráfico.

### Desactivar Traefik (Opcional)

Si prefieres acceso directo a los servicios sin Traefik:

1. Comenta la sección de Traefik en `docker-compose.prod.yml`
2. Expone los puertos directamente en cada servicio:

```yaml
# En cada servicio
ports:
  - "8001:8001" # catalog
  - "8002:8002" # payments
  # etc...
```

3. Elimina las labels de Traefik de los servicios

---

## 🎯 Patrón Saga

### ¿Qué es Saga?

El **patrón Saga** es un patrón de diseño para manejar transacciones distribuidas en arquitecturas de microservicios, donde no es posible usar transacciones ACID tradicionales.

### Nuestra Implementación

Este proyecto implementa **Saga con Orquestación**:

- ✅ El **Orchestrator** coordina toda la transacción
- ✅ Comunica directamente con cada microservicio vía HTTP
- ✅ Ejecuta compensaciones en orden reverso si hay fallo
- ✅ Mantiene estado completo de cada transacción

### Flujo de Compensación

Cuando una transacción falla, el orchestrator ejecuta compensaciones en **orden reverso**:

```
Creación (orden forward):
1. Catalog → OK
2. Payment → OK
3. Inventory → FAIL ❌

Compensación (orden reverso):
1. Purchase → (no se creó, skip)
2. Inventory → COMPENSATE (restaurar stock) ✅
3. Payment → REFUND ✅
```

### Estados de Transacción

- `COMPLETED` - Transacción exitosa (todos los pasos OK)
- `COMPENSATED` - Transacción fallida y revertida

### Probabilidades

Dado que cada servicio tiene diferentes tasas de fallo (excepto catalog que siempre es OK):

- **Payments:** 95% éxito
- **Inventory:** 70% éxito  
- **Purchases:** 95% éxito

**Probabilidad de éxito total:** 0.95 × 0.70 × 0.95 = **63.2%**  
**Probabilidad de fallo:** **36.8%**

---

## 💻 Requisitos Previos

### Software Necesario

1. **Docker** 24.0 o superior

   ```bash
   docker --version
   # Docker version 24.0.0 o superior
   ```

2. **Docker Compose** 2.20 o superior

   ```bash
   docker compose version
   # Docker Compose version v2.20.0 o superior
   ```

3. **Git**

   ```bash
   git --version
   # git version 2.30.0 o superior
   ```

4. **(Opcional) curl** - Para testing de APIs

   ```bash
   curl --version
   ```

5. **(Opcional) jq** - Para formatear JSON
   ```bash
   jq --version
   ```

### Recursos del Sistema

- **RAM:** Mínimo 4 GB (Recomendado 8 GB)
- **Disco:** Mínimo 5 GB libres
- **CPU:** 2 cores mínimo
- **Puertos disponibles:** 80 (Traefik), 8080 (Traefik Dashboard)

### Red de Traefik

El proyecto requiere una red externa de Docker llamada `traefik-public`. Si no existe, créala:

```bash
docker network create traefik-public
```

---

## 📥 Instalación

### 1. Clonar el Repositorio

```bash
git clone https://github.com/Zapallo-Code/ecommerce-microservices.git
cd ecommerce-microservices
```

### 2. Verificar Estructura del Proyecto

```bash
tree -L 2 -d
```

Deberías ver:

```
.
├── catalog/
│   ├── main/
│   └── products/
├── inventory/
│   ├── config/
│   └── inventory/
├── orchestrator/
│   └── app/
├── payments/
│   ├── app/
│   └── main/
├── purchases/
│   ├── app/
│   └── main/
└── scripts/
```

### 3. Revisar Archivos Docker

- `docker-compose.yml` - Para desarrollo
- `docker-compose.prod.yml` - Para producción (recomendado)
- Cada microservicio tiene su `Dockerfile`

---

## ⚙️ Configuración

### Variables de Entorno

El proyecto incluye archivos de ejemplo para configurar las variables de entorno:

- `.env.example` - Plantilla para desarrollo
- `.env.example.prod` - Plantilla para producción

#### Configuración Rápida

```bash
# Desarrollo
cp .env.example .env

# Producción
cp .env.example.prod .env.prod
```

#### Variables Principales

| Variable | Descripción | Valor por defecto |
|----------|-------------|-------------------|
| `POSTGRES_USER` | Usuario PostgreSQL | postgres |
| `POSTGRES_PASSWORD` | Contraseña PostgreSQL | postgres |
| `CATALOG_SECRET_KEY` | Secret key Django Catalog | (generado) |
| `PAYMENTS_SECRET_KEY` | Secret key Django Payments | (generado) |
| `INVENTORY_SECRET_KEY` | Secret key Django Inventory | (generado) |
| `PURCHASES_SECRET_KEY` | Secret key Django Purchases | (generado) |
| `LOG_LEVEL` | Nivel de logging | INFO |
| `CORS_ALLOWED_ORIGINS` | Orígenes CORS permitidos | * |

#### Generar Secret Keys para Producción

```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

---

## 🚀 Ejecución

### Requisitos Previos

1. Crear la red de Traefik (si no existe):

```bash
docker network create traefik-public
```

2. Tener Traefik corriendo (ver sección Traefik más abajo)

### Opción 1: Docker Compose Desarrollo

```bash
# Copiar configuración
cp .env.example .env

# Iniciar servicios
docker compose up --build -d

# Ver logs
docker compose logs -f
```

### Opción 2: Docker Compose Producción - **RECOMENDADO**

```bash
# Copiar configuración de producción
cp .env.example.prod .env.prod

# Editar .env.prod con valores seguros
# nano .env.prod

# Iniciar servicios
docker compose -f docker-compose.prod.yml --env-file .env.prod up --build -d
```

**Explicación de flags:**

- `-f docker-compose.prod.yml` - Usa el archivo de producción
- `--env-file .env.prod` - Usa variables de entorno de producción
- `--build` - Reconstruye las imágenes
- `-d` - Modo detached (background)

#### Verificar estado de servicios:

```bash
# Desarrollo
docker compose ps

# Producción
docker compose -f docker-compose.prod.yml ps
```

Deberías ver todos los servicios con estado `healthy`:

```
NAME                     STATUS
ecommerce-catalog        Up (healthy)
ecommerce-inventory      Up (healthy)
ecommerce-orchestrator   Up (healthy)
ecommerce-payments       Up (healthy)
ecommerce-postgres       Up (healthy)
ecommerce-purchases      Up (healthy)
```

#### Ver logs de un servicio:

```bash
# Logs del orchestrator
docker logs ecommerce-orchestrator -f

# Logs de payments
docker logs ecommerce-payments -f

# Logs de todos los servicios
docker compose logs -f
```

#### Detener servicios:

```bash
# Desarrollo
docker compose down

# Producción
docker compose -f docker-compose.prod.yml down
```

#### Detener y eliminar volúmenes (limpieza completa):

```bash
docker compose -f docker-compose.prod.yml down -v
```

### Configurar Traefik

Si no tienes Traefik instalado, puedes usar el siguiente docker-compose:

```yaml
# traefik-compose.yml
services:
  traefik:
    image: traefik:v3.0
    container_name: traefik
    command:
      - "--api.insecure=true"
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
    ports:
      - "80:80"
      - "8080:8080"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    networks:
      - traefik-public

networks:
  traefik-public:
    external: true
```

```bash
docker compose -f traefik-compose.yml up -d
```

### Verificación de Salud

Para verificar que el sistema funciona correctamente:

```powershell
# PowerShell - Health check del saga
Invoke-RestMethod -Uri "http://localhost/api/saga/"
```

```bash
# Bash - Health check del saga
curl http://localhost/api/saga/
```

Ejecutar una transacción de prueba:

```powershell
# PowerShell
Invoke-RestMethod -Uri "http://localhost/api/saga/transaction" -Method POST -ContentType "application/json" -Body '{"user_id": "1", "amount": 100}'
```

```bash
# Bash
curl -X POST http://localhost/api/saga/transaction \
  -H "Content-Type: application/json" \
  -d '{"user_id": "1", "amount": 100}'
```

Deberías recibir una respuesta con `status: "COMPLETED"` o `status: "FAILED"` (con compensaciones ejecutadas).

### Creación de Migraciones (Primera Ejecución)

Las migraciones se crean automáticamente al iniciar los contenedores, pero si necesitas recrearlas:

```bash
# Catalog
docker exec ecommerce-catalog python manage.py makemigrations products
docker exec ecommerce-catalog python manage.py migrate

# Payments
docker exec ecommerce-payments python manage.py makemigrations app
docker exec ecommerce-payments python manage.py migrate

# Inventory
docker exec ecommerce-inventory python manage.py makemigrations inventory
docker exec ecommerce-inventory python manage.py migrate

# Purchases
docker exec ecommerce-purchases python manage.py makemigrations app
docker exec ecommerce-purchases python manage.py migrate
```

---

## 📡 API Endpoints

### Endpoint Principal - Transacción Saga

Este es el único endpoint que necesitas para probar el sistema completo:

#### POST /api/saga/transaction

**URL:** `http://localhost/api/saga/transaction`

**Request Body:**
```json
{
  "user_id": "1",
  "amount": 100
}
```

**Ejemplo con PowerShell:**
```powershell
Invoke-RestMethod -Uri "http://localhost/api/saga/transaction" -Method POST -ContentType "application/json" -Body '{"user_id": "1", "amount": 100}'
```

**Ejemplo con curl:**
```bash
curl -X POST http://localhost/api/saga/transaction \
  -H "Content-Type: application/json" \
  -d '{"user_id": "1", "amount": 100}'
```

**Respuesta Exitosa (COMPLETED):**
```json
{
  "transaction_id": "e8065740-3844-4026-b366-be1d15580f64",
  "status": "COMPLETED",
  "steps": {
    "catalog": {"status": "success", "product": {...}},
    "payment": {"status": "success", "payment_id": 35},
    "inventory": {"status": "success"},
    "purchase": {"status": "success", "purchase_id": 12}
  },
  "timestamp": "2025-12-01T04:09:06.888287"
}
```

**Respuesta con Fallo (FAILED - con compensación):**
```json
{
  "transaction_id": "24f59cbe-0b89-427c-8180-2c3b6c8967b8",
  "status": "FAILED",
  "failed_step": "inventory",
  "error": "Sin stock disponible",
  "compensations": ["payment refunded"],
  "timestamp": "2025-12-01T04:06:24.487881"
}
```

#### GET /api/saga/ - Health Check

```bash
curl http://localhost/api/saga/
```

**Respuesta:**
```json
{
  "status": "healthy",
  "service": "saga-orchestrator"
}
```

#### GET /api/saga/status/{transaction_id} - Consultar Estado

```bash
curl http://localhost/api/saga/status/e8065740-3844-4026-b366-be1d15580f64
```

#### GET /api/saga/transactions - Listar Transacciones

```bash
curl http://localhost/api/saga/transactions
```

### Catalog (Puerto 8001)

#### Obtener Producto Aleatorio

```bash
curl http://localhost/api/catalog/products/random/
```

**Respuesta (siempre 200):**

```json
{
  "product_id": 1,
  "name": "Product-9377",
  "description": "Random product description 35",
  "price": "491.80",
  "category": "Electronics",
  "stock": 76
}
```

### Payments (Puerto 8002)

#### 1. Crear Pago (5% fallo)

```bash
curl -X POST http://localhost/api/payments/payments/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user-123",
    "transaction_id": "txn-456",
    "amount": 99.99
  }'
```

#### 2. Reembolsar Pago (Compensación)

```bash
curl -X POST http://localhost/api/payments/payments/42/refund/
```

### Inventory (Puerto 8003)

#### 1. Decrementar Inventario (30% fallo)

```bash
curl -X POST http://localhost/api/inventory/inventory/decrease/ \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": 1,
    "quantity": 2,
    "operation_id": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

#### 2. Compensar Inventario (Restaurar stock)

```bash
curl -X POST http://localhost/api/inventory/inventory/compensate/ \
  -H "Content-Type: application/json" \
  -d '{
    "operation_id": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

### Purchases (Puerto 8004)

#### 1. Crear Compra (5% fallo)

```bash
curl -X POST http://localhost/api/purchases/purchases/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user-123",
    "transaction_id": "txn-456",
    "product_id": "1",
    "payment_id": "42",
    "amount": 99.99
  }'
```

#### 2. Cancelar Compra (Compensación)

```bash
curl -X DELETE http://localhost/api/purchases/purchases/txn-456/cancel/
```

---

## 🏗 Arquitectura Técnica

### Stack Tecnológico por Capa

#### Capa de Presentación (API Gateway)

- **Orchestrator (FastAPI)**: Punto de entrada único para clientes

#### Capa de Negocio (Microservicios)

- **Catalog (Django)**: Lógica de productos
- **Payments (Django)**: Lógica de pagos
- **Inventory (Django)**: Lógica de inventario
- **Purchases (Django)**: Lógica de compras

#### Capa de Datos

- **PostgreSQL**: 4 bases de datos independientes
- **In-Memory Store**: Estado de transacciones en Orchestrator

### Comunicación entre Servicios

Todos los servicios se comunican a través de Traefik:

```
HTTP REST (Síncrono via Traefik)
┌─────────────┐
│ Orchestrator│
└──────┬──────┘
       │
       └─── http://traefik/api/* ───→ Traefik ───→ Services
```

El orchestrator usa las siguientes URLs para comunicarse:
- `http://traefik/api/catalog` → Catalog service
- `http://traefik/api/payments` → Payments service
- `http://traefik/api/inventory` → Inventory service
- `http://traefik/api/purchases` → Purchases service

### Gestión de Transacciones

```
┌──────────────────────────────────────┐
│  Transaction Store (In-Memory)       │
├──────────────────────────────────────┤
│ {                                    │
│   "transaction_id": "uuid",          │
│   "status": "COMPLETED|COMPENSATED", │
│   "payment_id": "...",               │
│   "inventory_updated": true|false,   │
│   "purchase_registered": true|false, │
│   "error_message": "...",            │
│   "created_at": "timestamp",         │
│   "completed_at": "timestamp"        │
│ }                                    │
└──────────────────────────────────────┘
```

### Resiliencia y Manejo de Errores

1. **Health Checks**: Cada servicio expone `/health/`
2. **Timeouts**: Configurados en HTTP client del orchestrator
3. **Retry Logic**: No implementado (fallo = compensación inmediata)
4. **Compensación Idempotente**: Compensaciones pueden ejecutarse múltiples veces

---

## 📚 Recursos Adicionales

### Documentación Oficial

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Docker Documentation](https://docs.docker.com/)

### Patrones y Arquitectura

- [Saga Pattern - Microsoft](https://docs.microsoft.com/en-us/azure/architecture/reference-architectures/saga/saga)
- [Microservices Patterns](https://microservices.io/patterns/index.html)
- [Distributed Transactions](https://martinfowler.com/articles/patterns-of-distributed-systems/)

### Herramientas Útiles

- [Postman](https://www.postman.com/) - Testing de APIs
- [HTTPie](https://httpie.io/) - Cliente HTTP CLI (alternativa a curl)
- [Portainer](https://www.portainer.io/) - UI para Docker

---

## 👥 Contribuciones

Este es un proyecto académico para demostrar el patrón Saga en microservicios.

### Estructura de Commits

```bash
git commit -m "tipo: descripción

- Detalle 1
- Detalle 2"
```

Tipos:

- `feat`: Nueva funcionalidad
- `fix`: Corrección de bug
- `docs`: Cambios en documentación
- `refactor`: Refactorización de código
- `test`: Añadir o modificar tests
- `chore`: Tareas de mantenimiento

---

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver archivo `LICENSE` para más detalles.

---

## 🎓 Miembros del equipo Zapallo-Code

- Valentin Rubio
- Luciano Castro
- Santiago Oses
- Santiago Calzolari
- Pablo Geyer
