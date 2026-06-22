from rest_framework import serializers

from products.serializers import ProductListSerializer
from .models import CartItem


class CartItemSerializer(serializers.ModelSerializer):
    """Позиция корзины для чтения: набор и стоимость строки."""

    product_detail = ProductListSerializer(source='product', read_only=True)
    line_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = CartItem
        fields = ('id', 'product', 'product_detail', 'quantity', 'line_total', 'created_at', 'updated_at')
        read_only_fields = ('id', 'created_at', 'updated_at')


class CartItemCreateSerializer(serializers.ModelSerializer):
    """Добавление или изменение позиции с контролем остатка."""

    class Meta:
        model = CartItem
        fields = ('id', 'product', 'quantity')

    def validate(self, attrs: dict) -> dict:
        product = attrs.get('product') or self.instance.product
        quantity = attrs.get('quantity', self.instance.quantity if self.instance else 1)
        if not product.is_active:
            raise serializers.ValidationError({'product': 'Этот набор временно недоступен.'})
        if product.stock <= 0:
            raise serializers.ValidationError({'product': 'Набор закончился на складе.'})
        if quantity > product.stock:
            raise serializers.ValidationError({'quantity': 'Запрошенное количество превышает остаток на складе.'})
        return attrs

    def create(self, validated_data: dict) -> CartItem:
        """Создаёт позицию или увеличивает количество существующей."""
        user = self.context['request'].user
        product = validated_data['product']
        quantity = validated_data.get('quantity', 1)
        item, created = CartItem.objects.get_or_create(user=user, product=product, defaults={'quantity': quantity})
        if not created:
            item.quantity += quantity
            if item.quantity > product.stock:
                raise serializers.ValidationError(
                    {'quantity': 'В корзине не может быть больше набора, чем есть на складе.'}
                )
            item.save(update_fields=('quantity', 'updated_at'))
        return item


class CartSummarySerializer(serializers.Serializer):
    """Свод по корзине: число позиций, единиц и итоговая сумма."""

    total_positions = serializers.IntegerField()
    total_quantity = serializers.IntegerField()
    total = serializers.DecimalField(max_digits=12, decimal_places=2)
