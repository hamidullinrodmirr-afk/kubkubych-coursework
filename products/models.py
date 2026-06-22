from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Category(models.Model):
    name = models.CharField('Серия LEGO', max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField('Описание', blank=True)

    class Meta:
        ordering = ('name',)
        verbose_name = 'серия'
        verbose_name_plural = 'серии'

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='products', verbose_name='Серия')
    name = models.CharField('Название', max_length=200)
    article = models.CharField('Артикул', max_length=40, unique=True)
    description = models.TextField('Описание')
    age_min = models.PositiveSmallIntegerField('Возраст от', validators=[MinValueValidator(0)])
    age_max = models.PositiveSmallIntegerField('Возраст до', validators=[MinValueValidator(0)])
    pieces = models.PositiveIntegerField('Количество деталей', validators=[MinValueValidator(1)])
    price = models.DecimalField('Цена', max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('1'))])
    discount_percent = models.PositiveSmallIntegerField('Скидка, %', default=0, validators=[MaxValueValidator(80)])
    stock = models.PositiveIntegerField('Остаток на складе', default=0)
    image_url = models.URLField('Ссылка на изображение', blank=True)
    is_active = models.BooleanField('Показывать в каталоге', default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('name',)
        verbose_name = 'набор'
        verbose_name_plural = 'наборы'

    def clean(self):
        if self.age_max < self.age_min:
            from django.core.exceptions import ValidationError
            raise ValidationError({'age_max': 'Максимальный возраст не может быть меньше минимального.'})

    @property
    def final_price(self):
        return (self.price * (Decimal('100') - self.discount_percent) / Decimal('100')).quantize(Decimal('0.01'))

    def __str__(self):
        return f'{self.article} — {self.name}'


class Favorite(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorites')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=('user', 'product'), name='unique_user_favorite')]
