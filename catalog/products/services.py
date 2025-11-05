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
    
    CATEGORIES = ["Electronics", "Computing", "Audio"]
    
    @staticmethod
    def simulate_latency() -> None:
        """Simulate network latency between 0.1 and 0.5 seconds"""
        time.sleep(random.uniform(0.1, 0.5))
    
    @staticmethod
    def generate_random_product() -> Dict:
        return {
            "id": random.randint(1000, 9999),
            "name": random.choice(ProductService.PRODUCT_NAMES),
            "price": round(random.uniform(100, 3000), 2),
            "category": random.choice(ProductService.CATEGORIES),
            "description": "High quality product",
            "stock": random.randint(1, 100)
        }
    