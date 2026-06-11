from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class Specialty(models.Model):
    """Справочник специализаций ветеринарной клиники."""

    name = models.CharField('Название', max_length=100, unique=True)
    description = models.TextField('Описание', blank=True)
    icon = models.ImageField('Иконка', upload_to='specialties/', blank=True, null=True)

    class Meta:
        verbose_name = 'Специализация'
        verbose_name_plural = 'Специализации'
        ordering = ['name']

    def __str__(self) -> str:
        return self.name


class Doctor(models.Model):
    """Профиль ветеринарного врача, связанный с учётной записью пользователя."""

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
    photo_url = models.URLField('Фото (ссылка)', blank=True, default='')
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

    def __str__(self) -> str:
        return f'{self.user.full_name} — {", ".join(s.name for s in self.specialties.all())}'


class Schedule(models.Model):
    """Интервал приёма врача в конкретный день недели, разбитый на слоты."""

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
    slot_duration = models.PositiveIntegerField(
        'Длительность слота (мин.)',
        default=30,
        validators=[MinValueValidator(15), MaxValueValidator(120)],
    )

    class Meta:
        verbose_name = 'Расписание'
        verbose_name_plural = 'Расписание'
        ordering = ['day_of_week', 'start_time']
        unique_together = ['doctor', 'day_of_week', 'start_time']

    def __str__(self) -> str:
        return (
            f'{self.doctor.user.full_name} — '
            f'{self.get_day_of_week_display()} '
            f'{self.start_time:%H:%M}–{self.end_time:%H:%M}'
        )

    def clean(self) -> None:
        """Валидация интервала приёма.

        Проверяет, что время начала раньше времени окончания и что интервал
        не пересекается с другими интервалами того же врача в тот же день.

        Raises:
            ValidationError: При нарушении любого из правил.
        """
        errors: dict[str, str] = {}

        if self.start_time and self.end_time and self.start_time >= self.end_time:
            errors['end_time'] = 'Время окончания должно быть позже времени начала'

        if not errors and self.doctor_id:
            overlapping = Schedule.objects.filter(
                doctor_id=self.doctor_id,
                day_of_week=self.day_of_week,
                start_time__lt=self.end_time,
                end_time__gt=self.start_time,
            ).exclude(pk=self.pk)
            if overlapping.exists():
                errors['start_time'] = (
                    'Интервал пересекается с другим расписанием врача в этот день'
                )

        if errors:
            raise ValidationError(errors)
