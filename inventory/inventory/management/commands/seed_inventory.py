"""
Management command to seed inventory data for testing.
This must be synchronized with catalog's seed_products command.
"""

from django.core.management.base import BaseCommand
from inventory.models import Inventory


class Command(BaseCommand):
    help = "Seed inventory with products matching catalog database"

    # Product IDs 1-10 matching the seed_products command in catalog
    # Each product gets inventory with reasonable stock levels
    SEED_INVENTORY = [
        {"product_id": 1, "stock": 50},    # Laptop Gaming Pro
        {"product_id": 2, "stock": 100},   # Wireless Headphones Elite
        {"product_id": 3, "stock": 75},    # Smart Watch Series X
        {"product_id": 4, "stock": 120},   # Mechanical Keyboard RGB
        {"product_id": 5, "stock": 40},    # 4K Ultra HD Monitor
        {"product_id": 6, "stock": 200},   # Wireless Gaming Mouse
        {"product_id": 7, "stock": 80},    # USB-C Docking Station
        {"product_id": 8, "stock": 150},   # Portable SSD 2TB
        {"product_id": 9, "stock": 90},    # Webcam 4K Pro
        {"product_id": 10, "stock": 110},  # Bluetooth Speaker Premium
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing inventory before seeding',
        )

    def handle(self, *args, **options):
        if options.get('clear'):
            self.stdout.write('Clearing existing inventory...')
            Inventory.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Cleared all inventory'))

        created_count = 0
        updated_count = 0

        for inventory_data in self.SEED_INVENTORY:
            inventory, created = Inventory.objects.update_or_create(
                product_id=inventory_data["product_id"],
                defaults={"stock": inventory_data["stock"], "reserved": 0},
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Created inventory for product {inventory.product_id} "
                        f"with {inventory.stock} units"
                    )
                )
            else:
                updated_count += 1
                self.stdout.write(
                    f"Updated inventory for product {inventory.product_id} "
                    f"with {inventory.stock} units"
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nSeeding complete! Created: {created_count}, Updated: {updated_count}'
            )
        )

        # List all inventory items
        self.stdout.write('\nCurrent inventory in database:')
        for inv in Inventory.objects.all():
            self.stdout.write(
                f'  Product ID: {inv.product_id} - Stock: {inv.stock} '
                f'(Reserved: {inv.reserved}, Available: {inv.available})'
            )
