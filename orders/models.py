from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator
from django.db import models
from django.utils import timezone

from .constants import ORDER_MAX_TOTAL, ORDER_MIN_TOTAL, ORDER_NUMBER_PREFIX, POSTAL_CODE_LENGTH

PHONE_VALIDATOR = RegexValidator(r'^\+?\d[\d\s\-()]{9,19}$', 'Укажите корректный номер телефона.')
POSTAL_CODE_VALIDATOR = RegexValidator(
    rf'^\d{{{POSTAL_CODE_LENGTH}}}$', f'Индекс должен состоять из {POSTAL_CODE_LENGTH} цифр.'
)


class Order(models.Model):
    """Заказ покупателя со снимком состава, адресом и статусной моделью."""

    class Status(models.TextChoices):
        NEW = 'new', 'Новый'
        PROCESSING = 'processing', 'В обработке'
        SHIPPED = 'shipped', 'Передан в доставку'
        DELIVERED = 'delivered', 'Доставлен'
        CANCELLED = 'cancelled', 'Отменён'

    class PaymentMethod(models.TextChoices):
        CASH = 'cash', 'Наличными при получении'
        CARD_ON_DELIVERY = 'card_on_delivery', 'Картой при получении'
        ONLINE = 'online_mock', 'Онлайн-оплата (демо)'

    # Допустимые переходы статусов: остальное запрещено.
    ALLOWED_TRANSITIONS = {
        Status.NEW: {Status.PROCESSING, Status.CANCELLED},
        Status.PROCESSING: {Status.SHIPPED, Status.CANCELLED},
        Status.SHIPPED: {Status.DELIVERED},
        Status.DELIVERED: set(),
        Status.CANCELLED: set(),
    }

    order_number = models.CharField('Номер заказа', max_length=24, unique=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='orders')
    recipient_name = models.CharField('Получатель', max_length=150)
    recipient_phone = models.CharField('Телефон', max_length=20, validators=[PHONE_VALIDATOR])
    city = models.CharField('Город', max_length=100)
    street = models.CharField('Улица', max_length=200)
    house = models.CharField('Дом', max_length=20)
    apartment = models.CharField('Квартира', max_length=20, blank=True)
    postal_code = models.CharField('Индекс', max_length=POSTAL_CODE_LENGTH, validators=[POSTAL_CODE_VALIDATOR])
    delivery_address = models.CharField('Адрес доставки', max_length=400, blank=True)
    payment_method = models.CharField('Оплата', max_length=20, choices=PaymentMethod.choices)
    status = models.CharField('Статус', max_length=20, choices=Status.choices, default=Status.NEW)
    total = models.DecimalField(
        'Сумма',
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(ORDER_MIN_TOTAL), MaxValueValidator(ORDER_MAX_TOTAL)],
    )
    comment = models.TextField('Комментарий', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField('Оплачен', null=True, blank=True)
    delivered_at = models.DateTimeField('Доставлен', null=True, blank=True)
    cancelled_at = models.DateTimeField('Отменён', null=True, blank=True)

    class Meta:
        ordering = ('-created_at',)
        verbose_name = 'заказ'
        verbose_name_plural = 'заказы'

    def __str__(self) -> str:
        return self.order_number or f'Заказ #{self.pk}'

    def save(self, *args, **kwargs) -> None:
        if not self.delivery_address:
            self.delivery_address = self.build_delivery_address()
        if not self.order_number:
            self.order_number = self._generate_order_number()
        super().save(*args, **kwargs)

    def _generate_order_number(self) -> str:
        """Человекочитаемый номер вида KK-20260623-0007."""
        day = timezone.now().strftime('%Y%m%d')
        prefix = f'{ORDER_NUMBER_PREFIX}-{day}'
        last = Order.objects.filter(order_number__startswith=prefix).count()
        return f'{prefix}-{last + 1:04d}'

    def build_delivery_address(self) -> str:
        """Собирает строку адреса из отдельных полей."""
        parts = [self.postal_code, self.city, f'ул. {self.street}', f'д. {self.house}']
        if self.apartment:
            parts.append(f'кв. {self.apartment}')
        return ', '.join(part for part in parts if part)

    def can_be_cancelled_by_user(self) -> bool:
        """Покупатель может отменить заказ только до отправки."""
        return self.status in (self.Status.NEW, self.Status.PROCESSING)

    def set_status(self, new_status: str) -> str:
        """Меняет статус с проверкой перехода и проставлением меток времени.

        Args:
            new_status: Целевой статус из ``Order.Status``.

        Returns:
            Прежний статус (для уведомлений).

        Raises:
            ValidationError: Если переход не разрешён.
        """
        if new_status not in self.ALLOWED_TRANSITIONS.get(self.status, set()):
            raise ValidationError({'status': 'Недопустимый переход статуса заказа.'})
        old_status = self.status
        self.status = new_status
        now = timezone.now()
        if new_status == self.Status.DELIVERED:
            self.delivered_at = now
        elif new_status == self.Status.CANCELLED:
            self.cancelled_at = now
        self.save(update_fields=('status', 'delivered_at', 'cancelled_at', 'updated_at'))
        return old_status


class OrderItem(models.Model):
    """Позиция заказа — снимок набора на момент покупки."""

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey('products.Product', on_delete=models.PROTECT, related_name='order_items')
    product_name = models.CharField('Название', max_length=200)
    product_article = models.CharField('Артикул', max_length=40)
    unit_price = models.DecimalField('Цена за штуку', max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField('Количество', validators=[MinValueValidator(1)])

    class Meta:
        constraints = [models.UniqueConstraint(fields=('order', 'product'), name='unique_order_product')]

    def __str__(self) -> str:
        return f'{self.product_name} × {self.quantity}'

    @property
    def line_total(self) -> Decimal:
        return (self.unit_price * self.quantity).quantize(Decimal('0.01'))
