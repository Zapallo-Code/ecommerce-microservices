# Saga Views - Documentación

Este módulo contiene endpoints especializados para el patrón Saga en el microservicio de Catálogo.

## Descripción

El patrón Saga es utilizado para manejar transacciones distribuidas en arquitecturas de microservicios. Este archivo implementa las operaciones necesarias para:

1. **Seleccionar productos** para una transacción
2. **Reservar stock** (fase de preparación)
3. **Confirmar reservas** (fase de commit)
4. **Compensar/Revertir** reservas (fase de rollback)

## Endpoints Disponibles

### 1. Obtener Producto Aleatorio

**Endpoint:** `GET /api/saga/products/random/`

**Descripción:** Retorna un producto aleatorio activo con stock disponible.

**Respuesta Exitosa (200):**
```json
{
    "product_id": 1,
    "name": "Laptop HP Pavilion 15",
    "price": "899.99",
    "description": "Laptop de alto rendimiento...",
    "stock": 15
}
```

**Características:**
- ✅ Solo productos activos (`is_active=True`)
- ✅ Solo productos con stock (`stock > 0`)
- ✅ Simulación de latencia (0.1-0.5s)
- ✅ 10% probabilidad de error 500

---

### 2. Reservar Stock de Producto

**Endpoint:** `POST /api/saga/products/reserve/`

**Descripción:** Reserva stock de un producto durante una transacción Saga.

**Request Body:**
```json
{
    "product_id": 1,
    "quantity": 2,
    "saga_transaction_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Respuesta Exitosa (200):**
```json
{
    "message": "Stock reserved successfully",
    "product_id": 1,
    "product_name": "Laptop HP Pavilion 15",
    "quantity_reserved": 2,
    "remaining_stock": 13,
    "saga_transaction_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Errores Posibles:**
- `400` - Datos inválidos
- `404` - Producto no encontrado o inactivo
- `409` - Stock insuficiente
- `500` - Error interno

**Características:**
- ✅ Usa transacciones atómicas de Django
- ✅ Lock pesimista (`select_for_update()`)
- ✅ Validación de stock disponible
- ✅ Logging detallado de operaciones

---

### 3. Confirmar Reserva

**Endpoint:** `POST /api/saga/products/confirm/`

**Descripción:** Confirma una reserva exitosa de stock.

**Request Body:**
```json
{
    "product_id": 1,
    "quantity": 2,
    "saga_transaction_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Respuesta Exitosa (200):**
```json
{
    "message": "Reservation confirmed successfully",
    "product_id": 1,
    "product_name": "Laptop HP Pavilion 15",
    "quantity_confirmed": 2,
    "current_stock": 13,
    "saga_transaction_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Notas:**
- El stock ya fue restado en la fase de reserva
- Esta fase registra la confirmación exitosa de la transacción

---

### 4. Compensar (Revertir) Reserva

**Endpoint:** `POST /api/saga/products/compensate/`

**Descripción:** Revierte una reserva de stock cuando la transacción Saga falla.

**Request Body:**
```json
{
    "product_id": 1,
    "quantity": 2,
    "saga_transaction_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Respuesta Exitosa (200):**
```json
{
    "message": "Compensation executed successfully",
    "product_id": 1,
    "product_name": "Laptop HP Pavilion 15",
    "quantity_restored": 2,
    "current_stock": 15,
    "saga_transaction_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Características:**
- ✅ Restaura el stock al estado previo
- ✅ Usa transacciones atómicas
- ✅ Lock pesimista para evitar race conditions
- ✅ Logging completo de compensaciones

---

### 5. Consultar Estado de Producto

**Endpoint:** `GET /api/saga/products/{product_id}/status/`

**Descripción:** Obtiene el estado actual de un producto.

**Respuesta Exitosa (200):**
```json
{
    "product_id": 1,
    "name": "Laptop HP Pavilion 15",
    "price": "899.99",
    "stock": 15,
    "is_active": true,
    "is_available": true,
    "category": "Computadoras",
    "last_updated": "2025-11-12T15:30:00Z"
}
```

---

## Flujo del Patrón Saga

### Escenario Exitoso:

```
1. Orquestador → GET /api/saga/products/random/
   ← Producto seleccionado

2. Orquestador → POST /api/saga/products/reserve/
   ← Stock reservado (restado)

3. [Otras operaciones en otros microservicios...]

4. Orquestador → POST /api/saga/products/confirm/
   ← Reserva confirmada ✅
```

### Escenario con Fallo:

```
1. Orquestador → GET /api/saga/products/random/
   ← Producto seleccionado

2. Orquestador → POST /api/saga/products/reserve/
   ← Stock reservado (restado)

3. [Fallo en otro microservicio ❌]

4. Orquestador → POST /api/saga/products/compensate/
   ← Stock restaurado (compensación ejecutada) ↩️
```

---

## Características de Seguridad

### Transacciones Atómicas
Todas las operaciones de escritura usan `transaction.atomic()` para garantizar consistencia.

### Locks Pesimistas
Se usa `select_for_update()` para evitar race conditions en operaciones concurrentes.

### Validación de Datos
- Validación de campos requeridos
- Validación de tipos de datos
- Validación de valores positivos

### Logging
Todas las operaciones son registradas con:
- Nivel INFO para operaciones exitosas
- Nivel WARNING para conflictos de negocio
- Nivel ERROR para errores del sistema

---

## Testing

### Ejemplo con curl:

```bash
# 1. Obtener producto aleatorio
curl http://localhost:8000/api/saga/products/random/

# 2. Reservar stock
curl -X POST http://localhost:8000/api/saga/products/reserve/ \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": 1,
    "quantity": 2,
    "saga_transaction_id": "test-123"
  }'

# 3. Confirmar reserva
curl -X POST http://localhost:8000/api/saga/products/confirm/ \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": 1,
    "quantity": 2,
    "saga_transaction_id": "test-123"
  }'

# O compensar si hay fallo
curl -X POST http://localhost:8000/api/saga/products/compensate/ \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": 1,
    "quantity": 2,
    "saga_transaction_id": "test-123"
  }'
```

---

## Integración con el Orquestador

El orquestador del Saga debe:

1. Generar un `saga_transaction_id` único (UUID recomendado)
2. Llamar a los endpoints en el orden correcto
3. Manejar timeouts y reintentos
4. Ejecutar compensaciones en orden inverso si hay fallos
5. Mantener un log de todas las operaciones para auditoría

---

## Mejoras Futuras

- [ ] Implementar tabla de reservas temporales
- [ ] Agregar TTL (Time To Live) para reservas
- [ ] Implementar idempotencia para reintentos
- [ ] Agregar métricas y monitoring
- [ ] Implementar circuit breaker
- [ ] Agregar rate limiting
