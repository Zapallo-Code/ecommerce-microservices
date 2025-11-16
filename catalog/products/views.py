"""
Catalog microservice views.
Simplified implementation following KISS principle.
Only provides the random product endpoint required by Saga orchestrator.
"""

import random
import time
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Product


class RandomProductView(APIView):
    """
    GET /products/random/

    Returns a random product with random data.
    Always returns status 200.
    No compensation required for this service.

    Simulates latency for realistic distributed system behavior.
    """

    def get(self, request):
        """
        Returns a random product.
        Always succeeds (status 200).
        """
        # Simulate latency (0.1 to 0.5 seconds)
        time.sleep(random.uniform(0.1, 0.5))

        # Get all active products with stock
        products = Product.objects.filter(is_active=True, stock__gt=0)

        if not products.exists():
            # If no products, create a random one
            product = Product.objects.create(
                name=f"Product-{random.randint(1000, 9999)}",
                description=f"Random product description {random.randint(1, 100)}",
                price=round(random.uniform(10.0, 500.0), 2),
                category=random.choice(
                    ["Electronics", "Clothing", "Books", "Food", "Toys"]
                ),
                stock=random.randint(10, 100),
                is_active=True,
            )
        else:
            # Select random product from existing ones
            product = random.choice(list(products))

        # Return product data
        return Response(
            {
                "product_id": product.id,
                "name": product.name,
                "description": product.description,
                "price": str(product.price),
                "category": product.category,
                "stock": product.stock,
            },
            status=status.HTTP_200_OK,
        )
