from rest_framework import serializers
from .models import Product


class ProductSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField(source="id", read_only=True)
    price = serializers.DecimalField(
        max_digits=10, decimal_places=2, coerce_to_string=True
    )

    class Meta:
        model = Product
        fields = ["product_id", "name", "description", "price", "category", "stock"]
        read_only_fields = ["product_id"]


class ProductRandomSerializer(serializers.ModelSerializer):
    product_id = serializers.IntegerField(source="id", read_only=True)

    class Meta:
        model = Product
        fields = ["product_id", "name", "description", "price", "category", "stock"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["price"] = str(data["price"])
        return data
