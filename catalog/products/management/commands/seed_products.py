"""
Management command to seed initial products in the catalog database.
"""
from django.core.management.base import BaseCommand
from products.models import Product

class Command(BaseCommand):
    help = 'Seed the database with initial products'

    # Pre-defined products for consistent seeding
    SEED_PRODUCTS = [
        {
            "name": "Laptop Gaming Pro",
            "description": "High-performance gaming laptop with RTX 4080, 32GB RAM, 1TB SSD",
            "price": 1899.99,
            "category": "Electronics",
            "stock": 50,
            "is_active": True,
        },
        {
            "name": "Wireless Headphones Elite",
            "description": "Premium noise-canceling headphones with 40h battery life",
            "price": 349.99,
            "category": "Electronics",
            "stock": 100,
            "is_active": True,
        },
        {
            "name": "Smart Watch Series X",
            "description": "Advanced smartwatch with health monitoring and GPS",
            "price": 449.99,
            "category": "Electronics",
            "stock": 75,
            "is_active": True,
        },
        {
            "name": "Mechanical Keyboard RGB",
            "description": "Mechanical gaming keyboard with Cherry MX switches and RGB",
            "price": 159.99,
            "category": "Electronics",
            "stock": 120,
            "is_active": True,
        },
        {
            "name": "4K Ultra HD Monitor",
            "description": "32-inch 4K monitor with HDR and 144Hz refresh rate",
            "price": 699.99,
            "category": "Electronics",
            "stock": 40,
            "is_active": True,
        },
        {
            "name": "Wireless Gaming Mouse",
            "description": "Professional gaming mouse with 25K DPI sensor",
            "price": 129.99,
            "category": "Electronics",
            "stock": 200,
            "is_active": True,
        },
        {
            "name": "USB-C Docking Station",
            "description": "Universal docking station with 12 ports for laptops",
            "price": 249.99,
            "category": "Electronics",
            "stock": 80,
            "is_active": True,
        },
        {
            "name": "Portable SSD 2TB",
            "description": "Ultra-fast portable SSD with USB 3.2 Gen 2",
            "price": 189.99,
            "category": "Electronics",
            "stock": 150,
            "is_active": True,
        },
        {
            "name": "Webcam 4K Pro",
            "description": "4K webcam with auto-focus and built-in microphone",
            "price": 199.99,
            "category": "Electronics",
            "stock": 90,
            "is_active": True,
        },
        {
            "name": "Bluetooth Speaker Premium",
            "description": "Portable waterproof speaker with 360° sound",
            "price": 179.99,
            "category": "Electronics",
            "stock": 110,
            "is_active": True,
        },
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing products before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing products...')
            Product.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Cleared all products'))

        created_count = 0
        updated_count = 0

        for product_data in self.SEED_PRODUCTS:
            product, created = Product.objects.update_or_create(
                name=product_data['name'],
                defaults=product_data
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created product: {product.name} (ID: {product.id})')
                )
            else:
                updated_count += 1
                self.stdout.write(
                    f'Updated product: {product.name} (ID: {product.id})'
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSeeding complete! Created: {created_count}, Updated: {updated_count}'
            )
        )
        
        # List all products with their IDs
        self.stdout.write('\nCurrent products in database:')
        for product in Product.objects.all():
            self.stdout.write(f'  ID: {product.id} - {product.name} (Stock: {product.stock})')
