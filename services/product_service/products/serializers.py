from rest_framework import serializers
from products.models import Product

class ProductSerilaizer(serializers.ModelSerializer):
    class Meta:
        model=Product
        fields="__all__"