import logging
import random
import time
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db import DatabaseError
from .models import Product
from .serializers import ProductRandomSerializer
from .services import ProductService, IProductService

logger = logging.getLogger(__name__)


class RandomProductView(APIView):
    def __init__(self, service: IProductService = None, **kwargs):
        super().__init__(**kwargs)
        self.service = service or ProductService()

    def post(self, request):
        logger.info(f"Random product request received with data: {request.data}")
        return self.get(request)

    def get(self, request):
        start_time = time.time()
        logger.info("Random product request received")

        try:
            # Simulate latency (0.1 to 0.5 seconds)
            latency = random.uniform(0.1, 0.5)
            time.sleep(latency)
            logger.debug(f"Simulated latency: {latency:.3f}s")

            # Get random product from service
            product = self.service.get_random_product()

            if not product:
                # If no products, create a random one
                logger.warning("No products found, creating random product")
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
                logger.info(f"Created new product: {product.id} - {product.name}")

            elapsed_time = time.time() - start_time
            logger.info(f"Random product request completed in {elapsed_time:.3f}s")

            # Return product data using serializer
            serializer = ProductRandomSerializer(product)
            return Response(serializer.data, status=status.HTTP_200_OK)

        except DatabaseError as e:
            logger.error(f"Database error in random product: {str(e)}", exc_info=True)
            return Response(
                {
                    "error": "Database error occurred",
                    "detail": "Unable to retrieve product",
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except Exception as e:
            logger.error(f"Unexpected error in random product: {str(e)}", exc_info=True)
            return Response(
                {"error": "Internal server error", "detail": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
