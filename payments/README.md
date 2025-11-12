# 💳 Payments Microservice

Microservicio de gestión de pagos para la plataforma de ecommerce.

## 🚀 Características

- Gestión de métodos de pago
- Procesamiento de transacciones
- Estados de pago (pending, processing, completed, failed, refunded, cancelled)
- Soporte para reembolsos
- API RESTful con Django REST Framework

## 📋 Endpoints Disponibles

### Métodos de Pago
- `GET /api/payments/methods/` - Listar métodos de pago activos
- `GET /api/payments/methods/{id}/` - Detalle de un método de pago

### Pagos
- `GET /api/payments/` - Listar todos los pagos
- `GET /api/payments/?order_id={id}` - Filtrar pagos por orden
- `POST /api/payments/` - Crear un nuevo pago
- `GET /api/payments/{id}/` - Detalle de un pago
- `POST /api/payments/{id}/process/` - Procesar un pago
- `POST /api/payments/{id}/refund/` - Reembolsar un pago
- `POST /api/payments/{id}/cancel/` - Cancelar un pago

## 🛠️ Configuración

### Variables de Entorno

```env
# Django
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=*

# Database
DB_NAME=payments_db
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432
```

### Instalación Local

1. Instalar dependencias:
```bash
uv sync
```

2. Crear migraciones:
```bash
python manage.py makemigrations
python manage.py migrate
```

3. Crear superusuario (opcional):
```bash
python manage.py createsuperuser
```

4. Ejecutar servidor:
```bash
python manage.py runserver
```

## 🧪 Tests

Ejecutar todos los tests:
```bash
python manage.py test
```

Ejecutar tests con cobertura:
```bash
coverage run --source='.' manage.py test
coverage report
```

## 📊 Modelos

### PaymentMethod
- `name`: Nombre del método de pago
- `description`: Descripción
- `is_active`: Si está activo o no

### Payment
- `order_id`: ID de la orden (del microservicio de purchases)
- `amount`: Monto del pago
- `currency`: Moneda (default: ARS)
- `status`: Estado del pago
- `payment_method`: Método de pago utilizado
- `transaction_id`: ID de transacción externa
- `error_message`: Mensaje de error si falla
- `metadata`: Información adicional (JSON)

## 🔄 Flujo de Estados

```
PENDING → PROCESSING → COMPLETED
                    ↓
                  FAILED
                  
COMPLETED → REFUNDED

PENDING/PROCESSING → CANCELLED
```

## 🐳 Docker

Construir imagen:
```bash
docker build -t payments-service .
```

Ejecutar contenedor:
```bash
docker run -p 8002:8002 payments-service
```

## 📝 Ejemplos de Uso

### Crear un nuevo pago
```bash
curl -X POST http://localhost:8002/api/payments/ \
  -H "Content-Type: application/json" \
  -d '{
    "order_id": "ORDER-123",
    "amount": "1500.50",
    "currency": "ARS",
    "payment_method": 1
  }'
```

### Procesar un pago
```bash
curl -X POST http://localhost:8002/api/payments/1/process/ \
  -H "Content-Type: application/json" \
  -d '{
    "status": "completed",
    "transaction_id": "TXN-ABC123"
  }'
```

### Reembolsar un pago
```bash
curl -X POST http://localhost:8002/api/payments/1/refund/ \
  -H "Content-Type: application/json" \
  -d '{
    "reason": "Cliente solicitó devolución"
  }'
```
