"""Бизнес-операции над заказами: атомарное оформление, отмена, смена статуса."""

from decimal import Decimal

from django.db import transaction
from django.utils import timezone
from rest_framework import serializers

from cart.models import CartItem
from .constants import ORDER_MAX_TOTAL, ORDER_MIN_TOTAL
from .models import Order, OrderItem


@transaction.atomic
def create_order_from_cart(user, data: dict) -> Order:
    """Создаёт заказ из корзины атомарно: блокировка, проверка остатка, списание.

    Args:
        user: Покупатель, оформляющий заказ.
        data: Проверенные данные доставки и оплаты.

    Returns:
        Созданный заказ.

    Raises:
        serializers.ValidationError: Пустая корзина, нехватка остатка или
            сумма вне диапазона — заказ не создаётся, корзина не очищается.
    """
    cart_items = list(CartItem.objects.select_for_update().select_related('product').filter(user=user))
    if not cart_items:
        raise serializers.ValidationError({'cart': 'Корзина пуста.'})

    total = Decimal('0.00')
    for item in cart_items:
        product = item.product
        if not product.is_active or item.quantity > product.stock:
            raise serializers.ValidationError({'cart': f'Недостаточно набора «{product.name}» на складе.'})
        total += product.final_price * item.quantity

    if total < ORDER_MIN_TOTAL or total > ORDER_MAX_TOTAL:
        raise serializers.ValidationError(
            {'total': f'Сумма заказа должна быть от {ORDER_MIN_TOTAL} до {ORDER_MAX_TOTAL} ₽.'}
        )

    order = Order(user=user, total=total, **data)
    if order.payment_method == Order.PaymentMethod.ONLINE:
        order.paid_at = timezone.now()
    order.save()

    for item in cart_items:
        product = item.product
        OrderItem.objects.create(
            order=order,
            product=product,
            product_name=product.name,
            product_article=product.article,
            unit_price=product.final_price,
            quantity=item.quantity,
        )
        product.stock -= item.quantity
        product.save(update_fields=('stock', 'updated_at'))

    CartItem.objects.filter(user=user).delete()
    return order


def restore_stock(order: Order) -> None:
    """Возвращает остатки на склад по позициям заказа."""
    for item in order.items.select_related('product'):
        product = item.product
        product.stock += item.quantity
        product.save(update_fields=('stock', 'updated_at'))


@transaction.atomic
def change_order_status(order: Order, new_status: str) -> str:
    """Меняет статус заказа, возвращая остатки при отмене.

    Returns:
        Прежний статус заказа (для email-уведомления).
    """
    old_status = order.set_status(new_status)
    if new_status == Order.Status.CANCELLED:
        restore_stock(order)
    return old_status
