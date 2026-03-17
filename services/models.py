from django.db import models


class Service(models.Model):
    name = models.CharField('Название', max_length=200)
    description = models.TextField('Описание', blank=True)
    price = models.DecimalField('Стоимость (руб.)', max_digits=10, decimal_places=2)
    duration_minutes = models.PositiveIntegerField('Длительность (мин.)', default=30)
    specialty = models.ForeignKey(
        'doctors.Specialty',
        on_delete=models.CASCADE,
        related_name='services',
        verbose_name='Специализация',
    )
    photo = models.ImageField('Изображение', upload_to='services/', blank=True, null=True)
    is_active = models.BooleanField('Доступна', default=True)

    class Meta:
        verbose_name = 'Услуга'
        verbose_name_plural = 'Услуги'
        ordering = ['specialty', 'name']

    def __str__(self):
        return f'{self.name} — {self.price} ₽'
