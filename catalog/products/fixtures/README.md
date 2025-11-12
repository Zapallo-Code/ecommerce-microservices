# Fixtures de Productos

Este directorio contiene datos de ejemplo para el microservicio de catálogo.

## Archivo: sample_products.json

Contiene 10 productos de ejemplo para pruebas y desarrollo.

### Productos incluidos:

1. **Laptop HP Pavilion 15** - $899.99 (Computadoras)
2. **Mouse Logitech MX Master 3** - $99.99 (Accesorios)
3. **Teclado Mecánico Keychron K2** - $79.99 (Accesorios)
4. **Monitor LG UltraWide 34"** - $499.99 (Monitores)
5. **Auriculares Sony WH-1000XM5** - $349.99 (Audio)
6. **Webcam Logitech C920 HD Pro** - $79.99 (Accesorios)
7. **SSD Samsung 980 PRO 1TB** - $149.99 (Almacenamiento)
8. **Silla Gamer Secretlab Titan Evo** - $549.99 (Muebles)
9. **Router WiFi 6 TP-Link Archer AX73** - $129.99 (Redes)
10. **Tablet Apple iPad Air 5ta Gen** - $749.99 (Tablets)

## Uso

### Cargar los fixtures en la base de datos:

```bash
# Desde la carpeta catalog/
python manage.py loaddata sample_products.json
```

### Limpiar la base de datos antes de cargar:

```bash
# Eliminar todos los productos
python manage.py shell -c "from products.models import Product; Product.objects.all().delete()"

# Cargar los fixtures
python manage.py loaddata sample_products.json
```

### Verificar que se cargaron correctamente:

```bash
python manage.py shell -c "from products.models import Product; print(f'Total productos: {Product.objects.count()}')"
```

## Estructura del JSON

Cada producto tiene los siguientes campos:

- `name`: Nombre del producto (string)
- `description`: Descripción detallada (string)
- `price`: Precio en formato decimal (string)
- `category`: Categoría del producto (string)
- `stock`: Cantidad disponible en inventario (integer)
- `is_active`: Si el producto está activo (boolean)

## Notas

- Todos los productos tienen `is_active: true`
- Los stocks varían entre 8 y 60 unidades
- Los precios van desde $79.99 hasta $899.99
- Las categorías incluyen: Computadoras, Accesorios, Monitores, Audio, Almacenamiento, Muebles, Redes, y Tablets
