from typing import Optional, Protocol
from .models import Product


class IProductRepository(Protocol):
    def get_random_active_product(self) -> Optional[Product]: ...


class ProductRepository:
    def get_random_active_product(self) -> Optional[Product]:
        return Product.objects.filter(is_active=True, stock__gt=0).order_by("?").first()
