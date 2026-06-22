from django.db import transaction
from rest_framework import serializers

from cart.models import CartItem
from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ('id', 'product', 'product_name', 'article', 'unit_price', 'quantity')


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Order
        fields = ('id', 'recipient_name', 'phone', 'delivery_address', 'payment_method', 'status', 'status_display', 'total', 'items', 'created_at', 'updated_at')
        read_only_fields = ('status', 'total', 'created_at', 'updated_at')

    def validate_delivery_address(self, value):
        parts = [part.strip() for part in value.split(',')]
        if len(parts) < 4 or any(not part for part in parts):
            raise serializers.ValidationError('Укажите адрес в формате: город, улица, дом, индекс (квартира — при наличии).')
        return value

    def create(self, validated_data):
        user = self.context['request'].user
        with transaction.atomic():
            cart_items = list(CartItem.objects.select_for_update().select_related('product').filter(user=user))
            if not cart_items:
                raise serializers.ValidationError('Корзина пуста.')
            total = sum((item.product.final_price * item.quantity for item in cart_items), start=0)
            if total < 500 or total > 100000:
                raise serializers.ValidationError({'total': 'Сумма заказа должна быть от 500 до 100 000 рублей.'})
            for item in cart_items:
                if not item.product.is_active or item.quantity > item.product.stock:
                    raise serializers.ValidationError({'cart': f'Недостаточно набора «{item.product.name}» на складе.'})
            order = Order.objects.create(user=user, total=total, **validated_data)
            for item in cart_items:
                product = item.product
                OrderItem.objects.create(order=order, product=product, product_name=product.name, article=product.article, unit_price=product.final_price, quantity=item.quantity)
                product.stock -= item.quantity
                product.save(update_fields=('stock', 'updated_at'))
            CartItem.objects.filter(user=user).delete()
        return order


class OrderStatusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ('status',)

    def validate_status(self, value):
        allowed = {
            Order.Status.NEW: {Order.Status.PROCESSING, Order.Status.CANCELLED},
            Order.Status.PROCESSING: {Order.Status.SHIPPED, Order.Status.CANCELLED},
            Order.Status.SHIPPED: {Order.Status.DELIVERED},
            Order.Status.DELIVERED: set(),
            Order.Status.CANCELLED: set(),
        }
        if value not in allowed[self.instance.status]:
            raise serializers.ValidationError('Недопустимый переход статуса заказа.')
        return value
