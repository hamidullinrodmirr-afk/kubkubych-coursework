from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models


class Review(models.Model):
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Автор',
    )
    doctor = models.ForeignKey(
        'doctors.Doctor',
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name='Врач',
    )
    appointment = models.OneToOneField(
        'appointments.Appointment',
        on_delete=models.CASCADE,
        related_name='review',
        verbose_name='Приём',
    )
    rating = models.PositiveIntegerField(
        'Оценка',
        validators=[MinValueValidator(1), MaxValueValidator(5)],
    )
    text = models.TextField('Текст отзыва')
    is_approved = models.BooleanField('Одобрен', default=False)
    created_at = models.DateTimeField('Создан', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлён', auto_now=True)

    class Meta:
        verbose_name = 'Отзыв'
        verbose_name_plural = 'Отзывы'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.author.full_name} → {self.doctor.user.full_name}: {self.rating}★'
