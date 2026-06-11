from datetime import datetime, timedelta
from typing import Any

from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework import serializers

from .models import Appointment, MedicalRecord
from pets.serializers import PetShortSerializer
from doctors.serializers import DoctorListSerializer
from services.serializers import ServiceShortSerializer


class AppointmentCreateSerializer(serializers.ModelSerializer):
    """Создание записи на приём с валидацией бизнес-правил.

    Проверяются: принадлежность питомца, доступность врача, соответствие
    специализации врача и услуги, попадание времени в расписание и сетку
    слотов, отсутствие конфликтов с другими записями.
    """

    class Meta:
        model = Appointment
        fields = ('doctor', 'pet', 'service', 'date', 'time_slot', 'comment')

    def validate_date(self, value: Any) -> Any:
        """Дата приёма: не в прошлом и не дальше 30 дней вперёд.

        Args:
            value: Проверяемая дата.

        Returns:
            Дата без изменений.

        Raises:
            serializers.ValidationError: Если дата вне допустимого окна.
        """
        today = timezone.localdate()
        if value < today:
            raise serializers.ValidationError('Нельзя записаться на прошедшую дату')
        if value > today + timedelta(days=30):
            raise serializers.ValidationError('Запись доступна не более чем на 30 дней вперёд')
        return value

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Сквозная валидация записи по бизнес-правилам.

        Args:
            attrs: Данные сериализатора.

        Returns:
            Проверенные данные.

        Raises:
            serializers.ValidationError: При нарушении любого правила.
        """
        doctor = attrs['doctor']
        service = attrs['service']
        appt_date = attrs['date']
        time_slot = attrs['time_slot']
        user = self.context['request'].user

        if attrs['pet'].owner != user:
            raise serializers.ValidationError({'pet': 'Это не ваш питомец'})

        if not doctor.is_available:
            raise serializers.ValidationError({'doctor': 'Врач не принимает записи'})

        if not doctor.specialties.filter(id=service.specialty_id).exists():
            raise serializers.ValidationError(
                {'service': 'Врач не оказывает услуги данной специализации'}
            )

        now = timezone.localtime()
        if appt_date == now.date() and time_slot <= now.time():
            raise serializers.ValidationError(
                {'time_slot': 'Выбранное время уже прошло'}
            )

        day_of_week = appt_date.weekday()
        schedule = doctor.schedules.filter(
            day_of_week=day_of_week,
            start_time__lte=time_slot,
            end_time__gt=time_slot,
        ).first()
        if schedule is None:
            raise serializers.ValidationError(
                {'time_slot': 'Выбранное время не входит в расписание врача'}
            )

        slot_start = datetime.combine(appt_date, time_slot)
        day_start = datetime.combine(appt_date, schedule.start_time)
        day_end = datetime.combine(appt_date, schedule.end_time)
        offset_minutes = (slot_start - day_start).total_seconds() / 60
        if offset_minutes % schedule.slot_duration != 0:
            raise serializers.ValidationError(
                {'time_slot': 'Время не совпадает с сеткой слотов врача'}
            )
        if slot_start + timedelta(minutes=schedule.slot_duration) > day_end:
            raise serializers.ValidationError(
                {'time_slot': 'Слот не умещается до конца приёма врача'}
            )

        conflicting = Appointment.objects.filter(
            doctor=doctor,
            date=appt_date,
            time_slot=time_slot,
        ).exclude(status=Appointment.Status.CANCELLED)
        if conflicting.exists():
            raise serializers.ValidationError(
                {'time_slot': 'Этот временной слот уже занят'}
            )

        return attrs

    def create(self, validated_data: dict[str, Any]) -> Appointment:
        """Создаёт запись от имени текущего пользователя.

        Гонка двух одновременных запросов на один слот разрешается
        уникальным ограничением БД ``uniq_active_slot_per_doctor``.

        Args:
            validated_data: Проверенные данные сериализатора.

        Returns:
            Созданная запись на приём.

        Raises:
            serializers.ValidationError: Если слот заняли параллельным запросом.
        """
        validated_data['client'] = self.context['request'].user
        try:
            with transaction.atomic():
                return super().create(validated_data)
        except IntegrityError:
            raise serializers.ValidationError(
                {'time_slot': 'Этот временной слот уже занят'}
            )


class AppointmentListSerializer(serializers.ModelSerializer):
    """Строка списка записей с именами участников и статусом."""

    client_name = serializers.CharField(source='client.full_name', read_only=True)
    doctor_name = serializers.CharField(source='doctor.user.full_name', read_only=True)
    pet_name = serializers.CharField(source='pet.name', read_only=True)
    service_name = serializers.CharField(source='service.name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Appointment
        fields = (
            'id', 'client_name', 'doctor_name', 'pet_name', 'service_name',
            'date', 'time_slot', 'status', 'status_display', 'created_at',
        )


class AppointmentDetailSerializer(serializers.ModelSerializer):
    """Подробная карточка записи с вложенными объектами."""

    pet = PetShortSerializer(read_only=True)
    doctor_detail = DoctorListSerializer(source='doctor', read_only=True)
    service_detail = ServiceShortSerializer(source='service', read_only=True)
    client_name = serializers.CharField(source='client.full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Appointment
        fields = (
            'id', 'client_name', 'doctor_detail', 'pet', 'service_detail',
            'date', 'time_slot', 'status', 'status_display',
            'comment', 'cancel_reason', 'created_at', 'updated_at',
        )


class AppointmentCancelSerializer(serializers.Serializer):
    """Параметры отмены записи (опциональная причина)."""

    cancel_reason = serializers.CharField(required=False, allow_blank=True)


class MedicalRecordSerializer(serializers.ModelSerializer):
    """Медицинская карта по завершённому приёму.

    Питомец и врач выводятся из приёма автоматически и не принимаются
    от клиента; приём после создания карты менять нельзя.
    """

    doctor_name = serializers.CharField(source='doctor.user.full_name', read_only=True)
    pet_name = serializers.CharField(source='pet.name', read_only=True)

    class Meta:
        model = MedicalRecord
        fields = (
            'id', 'appointment', 'pet', 'pet_name', 'doctor', 'doctor_name',
            'diagnosis', 'treatment', 'recommendations', 'created_at',
        )
        read_only_fields = ('id', 'pet', 'doctor', 'created_at')

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Проверяет статус приёма, права врача и уникальность карты.

        Args:
            attrs: Данные сериализатора.

        Returns:
            Проверенные данные.

        Raises:
            serializers.ValidationError: Если приём не завершён, принадлежит
                другому врачу, карта уже существует либо приём меняется
                при редактировании.
        """
        appointment = attrs.get('appointment') or (
            self.instance.appointment if self.instance else None
        )
        if appointment is None:
            raise serializers.ValidationError({'appointment': 'Укажите приём'})

        if self.instance and attrs.get('appointment') and attrs['appointment'] != self.instance.appointment:
            raise serializers.ValidationError(
                {'appointment': 'Нельзя перенести карту на другой приём'}
            )

        if appointment.status != Appointment.Status.COMPLETED:
            raise serializers.ValidationError(
                {'appointment': 'Карта заполняется только по завершённому приёму'}
            )

        user = self.context['request'].user
        if user.role == 'veterinarian' and appointment.doctor.user_id != user.id:
            raise serializers.ValidationError(
                {'appointment': 'Это приём другого врача'}
            )

        if self.instance is None and MedicalRecord.objects.filter(appointment=appointment).exists():
            raise serializers.ValidationError(
                {'appointment': 'Карта по этому приёму уже создана'}
            )

        return attrs

    def create(self, validated_data: dict[str, Any]) -> MedicalRecord:
        """Создаёт карту, выводя питомца и врача из приёма.

        Args:
            validated_data: Проверенные данные сериализатора.

        Returns:
            Созданная медицинская карта.
        """
        appointment = validated_data['appointment']
        validated_data['pet'] = appointment.pet
        validated_data['doctor'] = appointment.doctor
        return super().create(validated_data)
