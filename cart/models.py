from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models

from products.models import Product


class CartItem(models.Model):
    """Позиция корзины покупателя: набор и его количество."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cart_items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='cart_items')
    quantity = models.PositiveIntegerField('Количество', default=1, validators=[MinValueValidator(1)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=('user', 'product'), name='unique_cart_product')]
        ordering = ('-updated_at',)

    def __str__(self) -> str:
        return f'{self.product} × {self.quantity}'

    @property
    def line_total(self) -> Decimal:
        """Стоимость позиции с учётом скидки набора."""
        return self.product.final_price * self.quantity

    def clean(self) -> None:
        """Запрещает недоступные наборы и превышение остатка."""
        if not self.product_id:
            return
        if not self.product.is_active:
            raise ValidationError({'product': 'Этот набор временно недоступен.'})
        if self.product.stock <= 0:
            raise ValidationError({'product': 'Набор закончился на складе.'})
        if self.quantity > self.product.stock:
            raise ValidationError({'quantity': 'Запрошенное количество превышает остаток на складе.'})
