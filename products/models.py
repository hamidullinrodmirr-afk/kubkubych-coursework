from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from simple_history.models import HistoricalRecords

from .constants import DEFAULT_CATEGORY_MAX_DISCOUNT, MAX_DISCOUNT_PERCENT


class Category(models.Model):
    """Серия конструкторов: City, Technic, Star Wars и т. п."""

    name = models.CharField('Серия LEGO', max_length=100, unique=True)
    slug = models.SlugField('Slug', unique=True)
    description = models.TextField('Описание', blank=True)
    image = models.ImageField('Изображение', upload_to='categories/', blank=True, null=True)
    is_active = models.BooleanField('Активна', default=True)
    max_discount_percent = models.PositiveSmallIntegerField(
        'Максимальная скидка серии, %',
        default=DEFAULT_CATEGORY_MAX_DISCOUNT,
        validators=[MaxValueValidator(MAX_DISCOUNT_PERCENT)],
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('name',)
        verbose_name = 'серия'
        verbose_name_plural = 'серии'
        constraints = [
            models.CheckConstraint(
                check=models.Q(max_discount_percent__gte=0) & models.Q(max_discount_percent__lte=MAX_DISCOUNT_PERCENT),
                name='category_max_discount_range',
            )
        ]

    def __str__(self) -> str:
        return self.name


class Product(models.Model):
    """LEGO-набор каталога с ценой, скидкой и остатком."""

    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products', verbose_name='Серия')
    name = models.CharField('Название', max_length=200)
    slug = models.SlugField('Slug', max_length=220, unique=True, allow_unicode=True, blank=True)
    article = models.CharField('Артикул', max_length=40, unique=True)
    description = models.TextField('Описание')
    age_from = models.PositiveSmallIntegerField('Возраст от', validators=[MinValueValidator(0)])
    age_to = models.PositiveSmallIntegerField('Возраст до', validators=[MinValueValidator(0)])
    pieces = models.PositiveIntegerField('Количество деталей', validators=[MinValueValidator(1)])
    price = models.DecimalField('Цена', max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('1'))])
    discount_percent = models.PositiveSmallIntegerField(
        'Скидка, %', default=0, validators=[MaxValueValidator(MAX_DISCOUNT_PERCENT)]
    )
    stock = models.PositiveIntegerField('Остаток на складе', default=0)
    image = models.ImageField('Изображение', upload_to='products/', blank=True, null=True)
    specification_file = models.FileField('Спецификация', upload_to='product-specifications/', blank=True)
    image_url = models.URLField('Ссылка на изображение', blank=True)
    is_active = models.BooleanField('Показывать в каталоге', default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    favorited_by_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='Favorite',
        related_name='favorite_products',
        blank=True,
        verbose_name='Добавили в избранное',
    )
    history = HistoricalRecords()

    class Meta:
        ordering = ('name',)
        verbose_name = 'набор'
        verbose_name_plural = 'наборы'

    def __str__(self) -> str:
        return f'{self.article} — {self.name}'

    def save(self, *args, **kwargs) -> None:
        """Гарантирует уникальный slug на основе названия и артикула."""
        if not self.slug:
            base = slugify(self.name, allow_unicode=True) or 'set'
            self.slug = f'{base}-{self.article}'.lower()
        super().save(*args, **kwargs)

    def clean(self) -> None:
        """Бизнес-валидация цены, скидки, остатка и возрастного диапазона."""
        errors: dict[str, str] = {}
        if self.price is not None and self.price <= 0:
            errors['price'] = 'Цена должна быть больше нуля.'
        if self.age_to is not None and self.age_from is not None and self.age_to < self.age_from:
            errors['age_to'] = 'Возраст «до» не может быть меньше возраста «от».'
        if self.discount_percent > MAX_DISCOUNT_PERCENT:
            errors['discount_percent'] = f'Скидка не может превышать {MAX_DISCOUNT_PERCENT}%.'
        if self.category_id and self.discount_percent > self.category.max_discount_percent:
            errors['discount_percent'] = (
                f'Скидка превышает лимит серии «{self.category.name}» '
                f'({self.category.max_discount_percent}%).'
            )
        if self.price is not None and self.final_price <= 0:
            errors['discount_percent'] = 'Итоговая цена со скидкой должна быть больше нуля.'
        if errors:
            raise ValidationError(errors)

    @property
    def final_price(self) -> Decimal:
        """Цена с учётом скидки, округлённая до копеек."""
        return (self.price * (Decimal('100') - self.discount_percent) / Decimal('100')).quantize(Decimal('0.01'))

    @property
    def discount_amount(self) -> Decimal:
        """Абсолютный размер скидки в рублях."""
        return (self.price - self.final_price).quantize(Decimal('0.01'))

    @property
    def in_stock(self) -> bool:
        return self.stock > 0

    def get_absolute_url(self) -> str:
        return reverse('product-detail', kwargs={'slug': self.slug})


class Favorite(models.Model):
    """Отметка «в избранном» между покупателем и набором."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorites')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at',)
        constraints = [models.UniqueConstraint(fields=('user', 'product'), name='unique_user_favorite')]

    def __str__(self) -> str:
        return f'{self.user} ♥ {self.product}'

    def clean(self) -> None:
        if self.product_id and not self.product.is_active:
            raise ValidationError({'product': 'Нельзя добавить в избранное недоступный набор.'})
