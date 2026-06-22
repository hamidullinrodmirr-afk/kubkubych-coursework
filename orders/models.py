from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models


class Order(models.Model):
    class Status(models.TextChoices):
        NEW = 'new', 'Новый'
        PROCESSING = 'processing', 'В обработке'
        SHIPPED = 'shipped', 'Передан в доставку'
        DELIVERED = 'delivered', 'Доставлен'
        CANCELLED = 'cancelled', 'Отменён'

    class PaymentMethod(models.TextChoices):
        CARD = 'card', 'Банковская карта'
        CASH = 'cash', 'При получении'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='orders')
    recipient_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=30)
    delivery_address = models.TextField()
    payment_method = models.CharField(max_length=20, choices=PaymentMethod.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    total = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(500)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created_at',)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('products.Product', on_delete=models.PROTECT, related_name='order_items')
    product_name = models.CharField(max_length=200)
    article = models.CharField(max_length=40)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()

    class Meta:
        constraints = [models.UniqueConstraint(fields=('order', 'product'), name='unique_order_product')]
