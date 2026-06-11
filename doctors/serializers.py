from typing import Any

from django.db.models import Avg
from rest_framework import serializers

from .models import Specialty, Doctor, Schedule


class SpecialtySerializer(serializers.ModelSerializer):
    """Специализация клиники (справочник)."""

    class Meta:
        model = Specialty
        fields = ('id', 'name', 'description', 'icon')


class ScheduleSerializer(serializers.ModelSerializer):
    """Интервал расписания врача с человекочитаемым днём недели."""

    day_display = serializers.CharField(source='get_day_of_week_display', read_only=True)

    class Meta:
        model = Schedule
        fields = ('id', 'day_of_week', 'day_display', 'start_time', 'end_time', 'slot_duration')


class DoctorListSerializer(serializers.ModelSerializer):
    """Карточка врача для каталога.

    Рейтинг и количество отзывов берутся из аннотаций queryset
    (``_avg_rating``, ``_reviews_count``); признак ``is_my_doctor``
    вычисляется по списку врачей из контекста сериализатора, который
    передаёт ``DoctorViewSet.get_serializer_context``.
    """

    full_name = serializers.SerializerMethodField()
    specialties = SpecialtySerializer(many=True, read_only=True)
    avg_rating = serializers.SerializerMethodField()
    reviews_count = serializers.SerializerMethodField()
    photo = serializers.SerializerMethodField()
    is_my_doctor = serializers.SerializerMethodField()

    class Meta:
        model = Doctor
        fields = (
            'id', 'full_name', 'specialties', 'experience_years',
            'photo', 'consultation_price', 'is_available',
            'avg_rating', 'reviews_count', 'is_my_doctor',
        )

    def get_full_name(self, obj: Doctor) -> str:
        """Полное имя врача (фамилия и имя)."""
        return obj.user.full_name

    def get_photo(self, obj: Doctor) -> str:
        """Абсолютная ссылка на фото врача либо внешний URL."""
        if obj.photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.photo.url)
            return obj.photo.url
        return obj.photo_url or ''

    def get_avg_rating(self, obj: Doctor) -> float:
        """Средний рейтинг по одобренным отзывам (0, если отзывов нет)."""
        if hasattr(obj, '_avg_rating'):
            return round(obj._avg_rating, 1) if obj._avg_rating else 0
        return round(obj.reviews.filter(is_approved=True).aggregate(
            avg=Avg('rating'))['avg'] or 0, 1)

    def get_reviews_count(self, obj: Doctor) -> int:
        """Количество одобренных отзывов о враче."""
        if hasattr(obj, '_reviews_count'):
            return obj._reviews_count
        return obj.reviews.filter(is_approved=True).count()

    def get_is_my_doctor(self, obj: Doctor) -> bool:
        """Был ли текущий пользователь на завершённом приёме у врача.

        Args:
            obj: Сериализуемый врач.

        Returns:
            True, если идентификатор врача есть в наборе
            ``visited_doctor_ids`` из контекста сериализатора.
        """
        visited: set[int] = self.context.get('visited_doctor_ids', set())
        return obj.id in visited


class DoctorDetailSerializer(DoctorListSerializer):
    """Подробная карточка врача с образованием, биографией и расписанием."""

    schedules = ScheduleSerializer(many=True, read_only=True)

    class Meta(DoctorListSerializer.Meta):
        fields = DoctorListSerializer.Meta.fields + (
            'education', 'bio', 'schedules',
        )


class DoctorCreateSerializer(serializers.ModelSerializer):
    """Создание профиля врача администратором."""

    specialty_ids = serializers.PrimaryKeyRelatedField(
        queryset=Specialty.objects.all(), many=True, write_only=True,
    )

    class Meta:
        model = Doctor
        fields = (
            'user', 'specialty_ids', 'experience_years', 'education',
            'bio', 'photo', 'consultation_price',
        )

    def create(self, validated_data: dict[str, Any]) -> Doctor:
        """Создаёт врача и привязывает выбранные специализации.

        Args:
            validated_data: Проверенные данные сериализатора.

        Returns:
            Созданный профиль врача.
        """
        specialties = validated_data.pop('specialty_ids')
        doctor = Doctor.objects.create(**validated_data)
        doctor.specialties.set(specialties)
        return doctor


class DoctorUpdateSerializer(serializers.ModelSerializer):
    """Редактирование профиля врача (администратором или самим врачом)."""

    specialty_ids = serializers.PrimaryKeyRelatedField(
        queryset=Specialty.objects.all(), many=True, write_only=True, required=False,
    )

    class Meta:
        model = Doctor
        fields = (
            'specialty_ids', 'experience_years', 'education', 'bio',
            'photo', 'photo_url', 'consultation_price', 'is_available',
        )

    def update(self, instance: Doctor, validated_data: dict[str, Any]) -> Doctor:
        """Обновляет поля профиля и, при передаче, набор специализаций.

        Args:
            instance: Редактируемый профиль врача.
            validated_data: Проверенные данные сериализатора.

        Returns:
            Обновлённый профиль врача.
        """
        specialties = validated_data.pop('specialty_ids', None)
        instance = super().update(instance, validated_data)
        if specialties is not None:
            instance.specialties.set(specialties)
        return instance
