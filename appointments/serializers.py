from datetime import date, timedelta
from django.utils import timezone
from rest_framework import serializers
from .models import Appointment, MedicalRecord
from pets.serializers import PetShortSerializer
from doctors.serializers import DoctorListSerializer
from services.serializers import ServiceShortSerializer


class AppointmentCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = ('doctor', 'pet', 'service', 'date', 'time_slot', 'comment')

    def validate_date(self, value):
        if value < date.today():
            raise serializers.ValidationError('Нельзя записаться на прошедшую дату')
        if value > date.today() + timedelta(days=30):
            raise serializers.ValidationError('Запись доступна не более чем на 30 дней вперёд')
        return value

    def validate(self, attrs):
        doctor = attrs['doctor']
        service = attrs['service']
        appt_date = attrs['date']
        time_slot = attrs['time_slot']
        user = self.context['request'].user

        # Проверка: питомец принадлежит клиенту
        if attrs['pet'].owner != user:
            raise serializers.ValidationError({'pet': 'Это не ваш питомец'})

        # Проверка: врач принимает записи
        if not doctor.is_available:
            raise serializers.ValidationError({'doctor': 'Врач не принимает записи'})

        # Проверка: специализация врача соответствует услуге
        if not doctor.specialties.filter(id=service.specialty_id).exists():
            raise serializers.ValidationError(
                {'service': 'Врач не оказывает услуги данной специализации'}
            )

        # Проверка: время входит в расписание врача
        day_of_week = appt_date.weekday()
        schedule = doctor.schedules.filter(
            day_of_week=day_of_week,
            start_time__lte=time_slot,
            end_time__gt=time_slot,
        )
        if not schedule.exists():
            raise serializers.ValidationError(
                {'time_slot': 'Выбранное время не входит в расписание врача'}
            )

        # Проверка: слот не занят
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

    def create(self, validated_data):
        validated_data['client'] = self.context['request'].user
        return super().create(validated_data)


class AppointmentListSerializer(serializers.ModelSerializer):
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
    cancel_reason = serializers.CharField(required=False, allow_blank=True)


class MedicalRecordSerializer(serializers.ModelSerializer):
    doctor_name = serializers.CharField(source='doctor.user.full_name', read_only=True)
    pet_name = serializers.CharField(source='pet.name', read_only=True)

    class Meta:
        model = MedicalRecord
        fields = (
            'id', 'appointment', 'pet', 'pet_name', 'doctor', 'doctor_name',
            'diagnosis', 'treatment', 'recommendations', 'created_at',
        )
        read_only_fields = ('id', 'created_at')
