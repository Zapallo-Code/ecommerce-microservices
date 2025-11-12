"""
Management command to seed inventory data for testing.
"""
from django.core.management.base import BaseCommand
from inventory.models import Inventory


class Command(BaseCommand):
    help = 'Seed inventory with sample products'

    def handle(self, *args, **kwargs):
        products = [
            {'product_id': 1, 'stock': 100},
            {'product_id': 2, 'stock': 50},
            {'product_id': 3, 'stock': 200},
            {'product_id': 4, 'stock': 75},
            {'product_id': 5, 'stock': 150},
        ]

        for product_data in products:
            inventory, created = Inventory.objects.get_or_create(
                product_id=product_data['product_id'],
                defaults={'stock': product_data['stock']}
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Created inventory for product {inventory.product_id} with {inventory.stock} units'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'Inventory for product {inventory.product_id} already exists'
                    )
                )

        self.stdout.write(self.style.SUCCESS('Inventory seeding completed!'))
