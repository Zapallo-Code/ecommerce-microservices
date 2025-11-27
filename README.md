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

El sistema está compuesto por **5 microservicios** independientes que se comunican a través de HTTP REST APIs, coordinados por un **orquestador Saga**:

```
┌────────────────────────────────────────────────────────────┐
│                    ORCHESTRATOR (FastAPI)                  │
│                    Puerto: 8000                            │
│                                                            │
│  • Coordina transacciones distribuidas                     │
│  • Ejecuta compensaciones en caso de fallo                 │
│  • Mantiene estado de transacciones                        │
└────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   CATALOG    │    │   PAYMENTS   │    │  INVENTORY   │
│   (Django)   │    │   (Django)   │    │   (Django)   │
│  Puerto:8001 │    │  Puerto:8002 │    │  Puerto:8003 │
│              │    │              │    │              │
│ • Productos  │    │ • Pagos      │    │ • Stock      │
│   aleatorios │    │ • Reembolsos │    │ • Decrementos│
│ • Siempre OK │    │ • 50% fallo  │    │ • 50% fallo  │
└──────────────┘    └──────────────┘    └──────────────┘
                            │
                            ▼
                    ┌──────────────┐
                    │  PURCHASES   │
                    │   (Django)   │
                    │  Puerto:8004 │
                    │              │
                    │ • Compras    │
                    │ • Cancela.   │
                    │ • 50% fallo  │
                    └──────────────┘
                            │
        ┌───────────────────┴───────────────────┐
        │                                       │
        ▼                                       ▼
┌──────────────────────────────────────────────────┐
│           PostgreSQL Database                    │
│                                                  │
│  • ms_catalog    (Productos)                     │
│  • ms_payments   (Pagos)                         │
│  • ms_inventory  (Inventario)                    │
│  • ms_purchases  (Compras)                       │
└──────────────────────────────────────────────────┘
```

### Flujo de una Transacción Saga

```
1. Cliente → POST /saga/transaction → Orchestrator
2. Orchestrator → GET /products/random/ → Catalog (siempre éxito)
3. Orchestrator → POST /payments/ → Payments (50% fallo aleatorio)
4. Si Payment OK → POST /inventory/decrease/ → Inventory (50% fallo)
5. Si Inventory OK → POST /purchases/ → Purchases (50% fallo)
6. Si todo OK → TRANSACTION COMPLETED ✅

En caso de fallo en cualquier paso:
- COMPENSACIÓN: Orchestrator ejecuta rollback:
  1. DELETE /purchases/{id}/cancel/ (si se creó)
  2. POST /payments/{id}/refund/ (si se creó)
  3. Inventory NO se compensa (según requerimientos)
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
- **Traefik 2.10** - Reverse proxy y API Gateway
- **uv 0.9** - Gestor de paquetes Python (ultra-rápido)
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
CATALOG_URL = "http://catalog:8001"
PAYMENTS_URL = "http://payments:8002"
INVENTORY_URL = "http://inventory:8003"
PURCHASES_URL = "http://purchases:8004"
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

- `GET /health/` - Health check
- `GET /products/random/` - Obtener producto aleatorio (siempre éxito)

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

- **50% de probabilidad de fallo aleatorio** en creación de pagos
- Retorna 200 (éxito) o 409 (conflicto/error)
- Implementa endpoint de compensación (refund)
- Simula latencia de 0.1 a 0.3 segundos

#### Endpoints:

- `GET /health/` - Health check
- `POST /payments/` - Crear pago (50% fallo aleatorio)
- `POST /payments/{id}/refund/` - Reembolsar pago (compensación)

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

- **50% de probabilidad de fallo aleatorio** en decrementos
- Retorna 200 (éxito) o 409 (stock insuficiente)
- **NO tiene endpoint de compensación** (según requerimientos)
- Simula latencia de 0.1 a 0.3 segundos

#### Endpoints:

- `GET /health/` - Health check
- `POST /inventory/decrease/` - Decrementar inventario (50% fallo)

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
- **Tabla:** `inventory_inventory`

**⚠️ Importante:** Este servicio NO implementa restauración de inventario en caso de fallo (según diseño del Saga).

---

### 5. Purchases (Puerto 8004)

**Tecnología:** Django + Django REST Framework  
**Responsabilidad:** Registrar compras y manejar cancelaciones

#### Características:

- **50% de probabilidad de fallo aleatorio** en creación
- Retorna 200 (éxito) o 409 (conflicto)
- Implementa endpoint de compensación (cancel)
- Simula latencia de 0.1 a 0.3 segundos

#### Endpoints:

- `GET /health/` - Health check
- `POST /purchases/` - Crear compra (50% fallo aleatorio)
- `DELETE /purchases/{id}/cancel/` - Cancelar compra (compensación)

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

**Traefik** es un reverse proxy y load balancer moderno diseñado específicamente para microservicios. En este proyecto, Traefik actúa como puerta de entrada única (API Gateway) que enruta las peticiones a los microservicios correspondientes.

### Configuración en el Proyecto

Traefik está configurado en `docker-compose.prod.yml` y expone el puerto **80** como punto de entrada único al sistema.

#### Características

- ✅ **Auto-descubrimiento**: Detecta automáticamente los contenedores Docker
- ✅ **Routing dinámico**: Enruta peticiones según etiquetas Docker
- ✅ **Health checks**: Monitorea la salud de los servicios
- ✅ **Dashboard**: Interfaz web para visualizar rutas y servicios
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
   /orchestrator       /catalog           /payments
        │                   │                   │
        ▼                   ▼                   ▼
   orchestrator:8000   catalog:8001      payments:8002

        ▼                   ▼
   /inventory         /purchases
        │                   │
        ▼                   ▼
   inventory:8003     purchases:8004
```

### Reglas de Enrutamiento

Traefik enruta las peticiones según el path:

| Path Original                     | Redirige a                   | Servicio     |
| --------------------------------- | ---------------------------- | ------------ |
| `http://localhost/orchestrator/*` | `http://orchestrator:8000/*` | Orchestrator |
| `http://localhost/catalog/*`      | `http://catalog:8001/*`      | Catalog      |
| `http://localhost/payments/*`     | `http://payments:8002/*`     | Payments     |
| `http://localhost/inventory/*`    | `http://inventory:8003/*`    | Inventory    |
| `http://localhost/purchases/*`    | `http://purchases:8004/*`    | Purchases    |

### Etiquetas Docker (Labels)

Cada servicio tiene etiquetas que Traefik lee para configurar el enrutamiento:

```yaml
# Ejemplo: Orchestrator
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.orchestrator.rule=PathPrefix(`/orchestrator`)"
  - "traefik.http.routers.orchestrator.entrypoints=web"
  - "traefik.http.services.orchestrator.loadbalancer.server.port=8000"
  - "traefik.http.middlewares.orchestrator-stripprefix.stripprefix.prefixes=/orchestrator"
  - "traefik.http.routers.orchestrator.middlewares=orchestrator-stripprefix"
```

**Explicación:**

- `traefik.enable=true` - Habilita Traefik para este servicio
- `PathPrefix(/orchestrator)` - Coincide con URLs que empiezan con /orchestrator
- `stripprefix` - Remueve el prefijo antes de enviar al servicio backend
- `loadbalancer.server.port` - Puerto interno del servicio

### Dashboard de Traefik

Accede al dashboard en: **http://localhost:8080**

El dashboard muestra:

- ✅ Servicios activos y su estado
- ✅ Routers configurados
- ✅ Middlewares aplicados
- ✅ Health checks en tiempo real

### Ejemplos de Uso con Traefik

#### Sin Traefik (acceso directo):

```bash
# Acceso directo a cada servicio
curl http://localhost:8000/saga/transaction  # Orchestrator
curl http://localhost:8001/products/random/  # Catalog
curl http://localhost:8002/health/           # Payments
```

#### Con Traefik (a través del puerto 80):

```bash
# Todo a través de Traefik en puerto 80
curl http://localhost/orchestrator/saga/transaction
curl http://localhost/catalog/products/random/
curl http://localhost/payments/health/
curl http://localhost/inventory/health/
curl http://localhost/purchases/health/
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
2. Payment → REFUND ✅
3. Inventory → (no se compensa según diseño)
```

### Estados de Transacción

- `COMPLETED` - Transacción exitosa (todos los pasos OK)
- `COMPENSATED` - Transacción fallida y revertida

### Probabilidades

Dado que cada servicio tiene 50% de fallo (excepto catalog):

- **Probabilidad de éxito:** 0.5 × 0.5 × 0.5 = **12.5%**
- **Probabilidad de fallo:** **87.5%**

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
- **Puertos disponibles:** 80 (Traefik), 8080 (Traefik Dashboard), 8000-8004 (microservicios), 5432 (PostgreSQL)

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

El sistema usa configuración por defecto en `docker-compose.prod.yml`:

#### Base de Datos (PostgreSQL)

```yaml
POSTGRES_USER: ecommerce_user
POSTGRES_PASSWORD: ecommerce_pass
POSTGRES_MULTIPLE_DATABASES: ms_catalog,ms_payments,ms_inventory,ms_purchases
```

#### Servicios Django

```yaml
DATABASE_HOST: postgres
DATABASE_PORT: 5432
DATABASE_USER: ecommerce_user
DATABASE_PASSWORD: ecommerce_pass
DJANGO_SETTINGS_MODULE: main.settings # o config.settings
```

#### Orchestrator (FastAPI)

```yaml
CATALOG_URL: http://catalog:8001
PAYMENTS_URL: http://payments:8002
INVENTORY_URL: http://inventory:8003
PURCHASES_URL: http://purchases:8004
```

### Personalización (Opcional)

Si necesitas cambiar configuraciones, crea un archivo `.env`:

```bash
# .env
POSTGRES_PASSWORD=mi_password_seguro
CATALOG_PORT=9001
PAYMENTS_PORT=9002
# etc...
```

---

## 🚀 Ejecución

### Opción 1: Docker Compose (Producción) - **RECOMENDADO**

#### Iniciar todos los servicios:

```bash
docker compose -f docker-compose.prod.yml up --build -d
```

**Explicación de flags:**

- `-f docker-compose.prod.yml` - Usa el archivo de producción
- `--build` - Reconstruye las imágenes
- `-d` - Modo detached (background)

#### Verificar estado de servicios:

```bash
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
docker compose -f docker-compose.prod.yml logs -f
```

#### Detener servicios:

```bash
docker compose -f docker-compose.prod.yml down
```

#### Detener y eliminar volúmenes (limpieza completa):

```bash
docker compose -f docker-compose.prod.yml down -v
```

### Opción 2: Docker Compose (Desarrollo)

```bash
docker compose up --build
```

### Verificación de Salud

Verifica que todos los servicios estén respondiendo:

```bash
# Health check de cada servicio
curl http://localhost:8001/health/  # Catalog
curl http://localhost:8002/health/  # Payments
curl http://localhost:8003/health/  # Inventory
curl http://localhost:8004/health/  # Purchases
```

Todos deben retornar algo similar a:

```json
{ "status": "healthy", "service": "catalog" }
```

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

> **Nota:** Todos los endpoints se pueden acceder de dos formas:
>
> 1. **Acceso directo**: `http://localhost:{puerto}/endpoint`
> 2. **A través de Traefik**: `http://localhost/{servicio}/endpoint`

### Orchestrator (Puerto 8000)

#### 1. Iniciar Transacción Saga

**Endpoint:** `POST /saga/transaction`

**Request Body:**

```json
{
  "user_id": "user-123",
  "product_id": 1,
  "amount": 99.99
}
```

**Ejemplo con curl:**

```bash
# Acceso directo
curl -X POST http://localhost:8000/saga/transaction \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user-123",
    "product_id": 1,
    "amount": 99.99
  }'

# A través de Traefik
curl -X POST http://localhost/orchestrator/saga/transaction \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user-123",
    "product_id": 1,
    "amount": 99.99
  }'
```

**Respuesta Exitosa (200):**

```json
{
  "transaction_id": "e8065740-3844-4026-b366-be1d15580f64",
  "status": "COMPLETED",
  "message": "Transaction completed successfully",
  "details": {
    "user_id": "user-123",
    "product_id": "1",
    "payment_id": "35",
    "amount": 99.99
  },
  "timestamp": "2025-11-14T04:09:06.888287"
}
```

**Respuesta Compensada (409):**

```json
{
  "transaction_id": "24f59cbe-0b89-427c-8180-2c3b6c8967b8",
  "status": "COMPENSATED",
  "message": "Transaction failed and was reverted",
  "details": {
    "user_id": "user-123",
    "product_id": null,
    "payment_id": null,
    "error": "409: payments conflict: Error processing payment"
  },
  "timestamp": "2025-11-14T04:06:24.487881"
}
```

#### 2. Consultar Estado de Transacción

**Endpoint:** `GET /saga/status/{transaction_id}`

**Ejemplo:**

```bash
curl http://localhost:8000/saga/status/e8065740-3844-4026-b366-be1d15580f64
```

**Respuesta:**

```json
{
  "transaction_id": "e8065740-3844-4026-b366-be1d15580f64",
  "status": "COMPLETED",
  "user_id": "user-123",
  "product_id": "1",
  "payment_id": "35",
  "inventory_updated": true,
  "purchase_registered": true,
  "amount": 99.99,
  "created_at": "2025-11-14T04:09:03.629029",
  "completed_at": "2025-11-14T04:09:06.888287",
  "error_message": null
}
```

#### 3. Listar Todas las Transacciones

**Endpoint:** `GET /saga/transactions`

**Ejemplo:**

```bash
curl http://localhost:8000/saga/transactions | jq
```

**Respuesta:**

```json
{
  "total": 16,
  "transactions": [
    {
      "transaction_id": "...",
      "status": "COMPLETED",
      "user_id": "user-123",
      ...
    },
    ...
  ]
}
```

### Catalog (Puerto 8001)

#### 1. Health Check

```bash
curl http://localhost:8001/health/
```

#### 2. Obtener Producto Aleatorio

```bash
curl http://localhost:8001/products/random/
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

#### 1. Health Check

```bash
curl http://localhost:8002/health/
```

#### 2. Crear Pago (50% fallo)

```bash
curl -X POST http://localhost:8002/payments/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user-123",
    "transaction_id": "txn-456",
    "amount": 99.99
  }'
```

**Respuesta Exitosa (200):**

```json
{
  "payment_id": 42,
  "status": "success",
  "message": "Payment processed successfully"
}
```

**Respuesta Error (409):**

```json
{
  "payment_id": 43,
  "status": "error",
  "message": "Error processing payment"
}
```

#### 3. Reembolsar Pago (Compensación)

```bash
curl -X POST http://localhost:8002/payments/42/refund/
```

**Respuesta:**

```json
{
  "status": "compensated",
  "message": "Payment refunded successfully",
  "payment_id": 42,
  "transaction_id": "txn-456",
  "user_id": "user-123",
  "amount": "99.99"
}
```

### Inventory (Puerto 8003)

#### 1. Health Check

```bash
curl http://localhost:8003/health/
```

#### 2. Decrementar Inventario (50% fallo)

```bash
curl -X POST http://localhost:8003/inventory/decrease/ \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": 1,
    "quantity": 2,
    "operation_id": "550e8400-e29b-41d4-a716-446655440000"
  }'
```

**Respuesta Exitosa (200):**

```json
{
  "status": "success",
  "message": "Inventory decreased successfully",
  "product_id": "1",
  "remaining_quantity": 98
}
```

**Respuesta Error (409):**

```json
{
  "status": "error",
  "message": "Insufficient stock for product 1 (random failure)"
}
```

### Purchases (Puerto 8004)

#### 1. Health Check

```bash
curl http://localhost:8004/health/
```

#### 2. Crear Compra (50% fallo)

```bash
curl -X POST http://localhost:8004/purchases/ \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user-123",
    "transaction_id": "txn-456",
    "product_id": "1",
    "payment_id": "42",
    "amount": 99.99
  }'
```

**Respuesta Exitosa (200):**

```json
{
  "purchase_id": 15,
  "status": "success"
}
```

**Respuesta Error (409):**

```json
{
  "status": "error",
  "message": "Purchase failed",
  "error": "CONFLICT"
}
```

#### 3. Cancelar Compra (Compensación)

```bash
curl -X DELETE http://localhost:8004/purchases/15/cancel/
```

**Respuesta:**

```json
{
  "status": "success",
  "message": "Purchase cancelled successfully",
  "transaction_id": "15"
}
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

```
HTTP REST (Síncrono)
┌─────────────┐
│ Orchestrator│
└──────┬──────┘
       │
       ├─── HTTP POST ──→ Payments
       ├─── HTTP POST ──→ Inventory
       ├─── HTTP POST ──→ Purchases
       └─── HTTP GET ───→ Catalog
```

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
