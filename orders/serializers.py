from rest_framework import serializers

from .models import Order, OrderItem
from .services import change_order_status, create_order_from_cart


class OrderItemSerializer(serializers.ModelSerializer):
    """Позиция заказа со снимком названия, артикула и цены."""

    line_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = OrderItem
        fields = ('id', 'product', 'product_name', 'product_article', 'unit_price', 'quantity', 'line_total')


class OrderListSerializer(serializers.ModelSerializer):
    """Краткая карточка заказа для списка."""

    status_display = serializers.CharField(source='get_status_display', read_only=True)
    items_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Order
        fields = ('id', 'order_number', 'status', 'status_display', 'total', 'items_count', 'created_at')


class OrderDetailSerializer(serializers.ModelSerializer):
    """Полная карточка заказа с составом, адресом и метками времени."""

    items = OrderItemSerializer(many=True, read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    payment_display = serializers.CharField(source='get_payment_method_display', read_only=True)
    can_cancel = serializers.SerializerMethodField()

    class Meta:
        model = Order
        fields = (
            'id', 'order_number', 'status', 'status_display',
            'recipient_name', 'recipient_phone', 'city', 'street', 'house', 'apartment',
            'postal_code', 'delivery_address', 'payment_method', 'payment_display',
            'total', 'comment', 'items', 'can_cancel',
            'created_at', 'updated_at', 'paid_at', 'delivered_at', 'cancelled_at',
        )

    def get_can_cancel(self, obj: Order) -> bool:
        return obj.can_be_cancelled_by_user()


class OrderCreateSerializer(serializers.ModelSerializer):
    """Оформление заказа из корзины текущего покупателя."""

    class Meta:
        model = Order
        fields = (
            'recipient_name', 'recipient_phone', 'city', 'street', 'house',
            'apartment', 'postal_code', 'payment_method', 'comment',
        )

    def create(self, validated_data: dict) -> Order:
        return create_order_from_cart(self.context['request'].user, validated_data)


class OrderStatusUpdateSerializer(serializers.ModelSerializer):
    """Смена статуса заказа администратором с проверкой перехода."""

    old_status = serializers.CharField(read_only=True)

    class Meta:
        model = Order
        fields = ('status', 'old_status')

    def validate_status(self, value: str) -> str:
        if value not in self.instance.ALLOWED_TRANSITIONS.get(self.instance.status, set()):
            raise serializers.ValidationError('Недопустимый переход статуса заказа.')
        return value

    def update(self, instance: Order, validated_data: dict) -> Order:
        old_status = change_order_status(instance, validated_data['status'])
        instance.old_status = old_status
        return instance
