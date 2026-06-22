from rest_framework import serializers

from products.serializers import ProductSerializer
from .models import CartItem


class CartItemSerializer(serializers.ModelSerializer):
    product_detail = ProductSerializer(source='product', read_only=True)
    subtotal = serializers.SerializerMethodField()

    class Meta:
        model = CartItem
        fields = ('id', 'product', 'product_detail', 'quantity', 'subtotal', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')

    def get_subtotal(self, obj):
        return obj.product.final_price * obj.quantity

    def validate(self, attrs):
        product = attrs.get('product') or self.instance.product
        quantity = attrs.get('quantity', self.instance.quantity if self.instance else 1)
        if not product.is_active:
            raise serializers.ValidationError({'product': 'Этот набор временно недоступен.'})
        if quantity > product.stock:
            raise serializers.ValidationError({'quantity': 'Запрошенное количество превышает остаток на складе.'})
        return attrs

    def create(self, validated_data):
        user = self.context['request'].user
        product = validated_data['product']
        quantity = validated_data.get('quantity', 1)
        item, created = CartItem.objects.get_or_create(user=user, product=product, defaults={'quantity': quantity})
        if not created:
            item.quantity += quantity
            if item.quantity > product.stock:
                raise serializers.ValidationError({'quantity': 'В корзине не может быть больше товара, чем на складе.'})
            item.save(update_fields=('quantity', 'updated_at'))
        return item
