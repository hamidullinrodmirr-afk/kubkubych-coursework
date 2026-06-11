from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class Pet(models.Model):
    """Питомец клиента с базовыми данными о здоровье."""

    class Species(models.TextChoices):
        CAT = 'cat', 'Кошка'
        DOG = 'dog', 'Собака'
        BIRD = 'bird', 'Птица'
        RODENT = 'rodent', 'Грызун'
        REPTILE = 'reptile', 'Рептилия'
        OTHER = 'other', 'Другое'

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='pets',
        verbose_name='Владелец',
    )
    name = models.CharField('Кличка', max_length=50)
    species = models.CharField('Вид', max_length=20, choices=Species.choices)
    breed = models.CharField('Порода', max_length=100, blank=True)
    age = models.PositiveIntegerField(
        'Возраст (мес.)',
        validators=[MaxValueValidator(360)],
    )
    weight = models.DecimalField(
        'Вес (кг)',
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01')), MaxValueValidator(Decimal('200'))],
    )
    health_notes = models.TextField('Особенности здоровья', blank=True)
    photo = models.ImageField('Фото', upload_to='pets/', blank=True, null=True)
    created_at = models.DateTimeField('Дата добавления', auto_now_add=True)

    class Meta:
        verbose_name = 'Питомец'
        verbose_name_plural = 'Питомцы'
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f'{self.name} ({self.get_species_display()}) — {self.owner.full_name}'
