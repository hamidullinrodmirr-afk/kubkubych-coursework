from django.conf import settings
from django.db import models


class Specialty(models.Model):
    name = models.CharField('Название', max_length=100, unique=True)
    description = models.TextField('Описание', blank=True)
    icon = models.ImageField('Иконка', upload_to='specialties/', blank=True, null=True)

    class Meta:
        verbose_name = 'Специализация'
        verbose_name_plural = 'Специализации'
        ordering = ['name']

    def __str__(self):
        return self.name


class Doctor(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='doctor_profile',
        verbose_name='Пользователь',
    )
    specialties = models.ManyToManyField(
        Specialty,
        related_name='doctors',
        verbose_name='Специализации',
    )
    experience_years = models.PositiveIntegerField('Стаж (лет)', default=0)
    education = models.TextField('Образование', blank=True)
    bio = models.TextField('Биография', blank=True)
    photo = models.ImageField('Фото', upload_to='doctors/', blank=True, null=True)
    consultation_price = models.DecimalField(
        'Стоимость консультации (руб.)',
        max_digits=10,
        decimal_places=2,
        default=0,
    )
    is_available = models.BooleanField('Принимает записи', default=True)

    class Meta:
        verbose_name = 'Ветеринар'
        verbose_name_plural = 'Ветеринары'
        ordering = ['user__last_name']

    def __str__(self):
        return f'{self.user.full_name} — {", ".join(s.name for s in self.specialties.all())}'


class Schedule(models.Model):
    class DayOfWeek(models.IntegerChoices):
        MONDAY = 0, 'Понедельник'
        TUESDAY = 1, 'Вторник'
        WEDNESDAY = 2, 'Среда'
        THURSDAY = 3, 'Четверг'
        FRIDAY = 4, 'Пятница'
        SATURDAY = 5, 'Суббота'
        SUNDAY = 6, 'Воскресенье'

    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name='schedules',
        verbose_name='Врач',
    )
    day_of_week = models.IntegerField('День недели', choices=DayOfWeek.choices)
    start_time = models.TimeField('Начало приёма')
    end_time = models.TimeField('Конец приёма')
    slot_duration = models.PositiveIntegerField('Длительность слота (мин.)', default=30)

    class Meta:
        verbose_name = 'Расписание'
        verbose_name_plural = 'Расписание'
        ordering = ['day_of_week', 'start_time']
        unique_together = ['doctor', 'day_of_week', 'start_time']

    def __str__(self):
        return (
            f'{self.doctor.user.full_name} — '
            f'{self.get_day_of_week_display()} '
            f'{self.start_time:%H:%M}–{self.end_time:%H:%M}'
        )
