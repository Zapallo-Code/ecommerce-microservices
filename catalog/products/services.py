import random
import time
from typing import Dict

class ProductService:
    
    PRODUCT_NAMES = [
        "Laptop Dell XPS 15",
        "iPhone 15 Pro",
        "Samsung Galaxy S24",
        "Sony WH-1000XM5",
        "iPad Pro 12.9"
    ]
    
    CATEGORIES = ["Electrónica", "Computación", "Audio"]
    
    @staticmethod
    def simulate_latency() -> None:
        time.sleep(random.uniform(0.1, 0.5))
    
    @staticmethod
    def generate_random_product() -> Dict:

        return {
            "id": random.randint(1000, 9999),
            "name": random.choice(ProductService.PRODUCT_NAMES),
            "price": round(random.uniform(100, 3000), 2),
            "category": random.choice(ProductService.CATEGORIES),
            "description": "Producto de alta calidad",
            "stock": random.randint(1, 100)
        }
    