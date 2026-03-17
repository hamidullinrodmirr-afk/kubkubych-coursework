from django.conf import settings
from django.db import models


class Appointment(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'Ожидание'
        CONFIRMED = 'confirmed', 'Подтверждён'
        IN_PROGRESS = 'in_progress', 'В процессе'
        COMPLETED = 'completed', 'Завершён'
        CANCELLED = 'cancelled', 'Отменён'

    client = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='appointments',
        verbose_name='Клиент',
    )
    doctor = models.ForeignKey(
        'doctors.Doctor',
        on_delete=models.CASCADE,
        related_name='appointments',
        verbose_name='Врач',
    )
    pet = models.ForeignKey(
        'pets.Pet',
        on_delete=models.CASCADE,
        related_name='appointments',
        verbose_name='Питомец',
    )
    service = models.ForeignKey(
        'services.Service',
        on_delete=models.CASCADE,
        related_name='appointments',
        verbose_name='Услуга',
    )
    date = models.DateField('Дата приёма')
    time_slot = models.TimeField('Время начала')
    status = models.CharField(
        'Статус',
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    comment = models.TextField('Комментарий', blank=True)
    cancel_reason = models.TextField('Причина отмены', blank=True)
    created_at = models.DateTimeField('Создано', auto_now_add=True)
    updated_at = models.DateTimeField('Обновлено', auto_now=True)

    class Meta:
        verbose_name = 'Запись на приём'
        verbose_name_plural = 'Записи на приём'
        ordering = ['-date', '-time_slot']

    def __str__(self):
        return (
            f'{self.client.full_name} → {self.doctor.user.full_name} '
            f'({self.date} {self.time_slot:%H:%M})'
        )


class MedicalRecord(models.Model):
    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.CASCADE,
        related_name='medical_record',
        verbose_name='Приём',
    )
    pet = models.ForeignKey(
        'pets.Pet',
        on_delete=models.CASCADE,
        related_name='medical_records',
        verbose_name='Питомец',
    )
    doctor = models.ForeignKey(
        'doctors.Doctor',
        on_delete=models.CASCADE,
        related_name='medical_records',
        verbose_name='Врач',
    )
    diagnosis = models.TextField('Диагноз')
    treatment = models.TextField('Назначенное лечение')
    recommendations = models.TextField('Рекомендации', blank=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)

    class Meta:
        verbose_name = 'Медицинская карта'
        verbose_name_plural = 'Медицинские карты'
        ordering = ['-created_at']

    def __str__(self):
        return f'Карта: {self.pet.name} — {self.diagnosis[:50]}'
