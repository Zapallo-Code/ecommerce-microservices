# Tests - Microservicio de Catálogo

Esta carpeta contiene todos los tests del microservicio de catálogo.

## Estructura

```
tests/
├── __init__.py           # Inicialización del paquete de tests
├── test_models.py        # Tests para los modelos (Product)
├── test_api.py          # Tests para los endpoints de la API
└── README.md            # Esta documentación
```

## Tests Implementados

### Test de Modelos (`test_models.py`)

Tests para el modelo `Product`:

#### ProductModelTest
- ✅ `test_create_product` - Crear un producto correctamente
- ✅ `test_product_str_method` - Método `__str__` del modelo
- ✅ `test_product_is_available_property` - Propiedad `is_available`
- ✅ `test_product_price_validation` - Validación de precio
- ✅ `test_product_stock_can_be_zero` - Stock puede ser cero
- ✅ `test_product_default_values` - Valores por defecto
- ✅ `test_update_product` - Actualizar producto
- ✅ `test_delete_product` - Eliminar producto
- ✅ `test_filter_active_products` - Filtrar productos activos
- ✅ `test_filter_products_with_stock` - Filtrar productos con stock

**Total: 10 tests de modelos**

---

### Tests de API (`test_api.py`)

#### ProductAPITest
Tests para endpoints CRUD de productos:

- ✅ `test_list_products` - GET /api/products/
- ✅ `test_retrieve_product` - GET /api/products/{id}/
- ✅ `test_create_product` - POST /api/products/
- ✅ `test_update_product` - PUT /api/products/{id}/
- ✅ `test_partial_update_product` - PATCH /api/products/{id}/
- ✅ `test_delete_product` - DELETE /api/products/{id}/
- ✅ `test_filter_by_category` - Filtrar por categoría
- ✅ `test_filter_by_is_active` - Filtrar por estado activo
- ✅ `test_search_products` - Buscar productos
- ✅ `test_low_stock_action` - GET /api/products/low_stock/
- ✅ `test_out_of_stock_action` - GET /api/products/out_of_stock/
- ✅ `test_random_product_action` - GET /api/products/random/
- ✅ `test_create_product_invalid_price` - Validación de precio
- ✅ `test_create_product_invalid_stock` - Validación de stock
- ✅ `test_retrieve_nonexistent_product` - Producto no existe

**Subtotal: 15 tests de API de productos**

#### HealthCheckAPITest
Tests para endpoints de health check:

- ✅ `test_basic_health_check` - GET /catalog/health/
- ✅ `test_detailed_health_check` - GET /catalog/health/detailed/
- ✅ `test_readiness_check` - GET /catalog/health/ready/
- ✅ `test_liveness_check` - GET /catalog/health/live/

**Subtotal: 4 tests de health check**

#### SagaAPITest
Tests para endpoints del patrón Saga:

- ✅ `test_saga_random_product` - GET /api/saga/products/random/
- ✅ `test_saga_reserve_product` - POST /api/saga/products/reserve/
- ✅ `test_saga_reserve_insufficient_stock` - Reserva con stock insuficiente
- ✅ `test_saga_confirm_product` - POST /api/saga/products/confirm/
- ✅ `test_saga_compensate_product` - POST /api/saga/products/compensate/
- ✅ `test_saga_product_status` - GET /api/saga/products/{id}/status/

**Subtotal: 6 tests de Saga**

**Total tests de API: 25 tests**

---

## Resumen Total

- **Tests de Modelos:** 10
- **Tests de API:** 25
- **TOTAL:** 35 tests

---

## Ejecutar Tests

### Ejecutar todos los tests

```bash
# Desde la carpeta catalog/
python manage.py test tests
```

### Ejecutar solo tests de modelos

```bash
python manage.py test tests.test_models
```

### Ejecutar solo tests de API

```bash
python manage.py test tests.test_api
```

### Ejecutar una clase específica de tests

```bash
# Tests de productos
python manage.py test tests.test_api.ProductAPITest

# Tests de health check
python manage.py test tests.test_api.HealthCheckAPITest

# Tests de Saga
python manage.py test tests.test_api.SagaAPITest
```

### Ejecutar un test específico

```bash
python manage.py test tests.test_models.ProductModelTest.test_create_product
```

### Ejecutar tests con verbosidad

```bash
python manage.py test tests --verbosity=2
```

---

## Configuración de Tests

### Base de Datos de Tests

Django automáticamente crea una base de datos de prueba (SQLite en memoria) para ejecutar los tests, lo que hace que sean rápidos y no afecten los datos de desarrollo.