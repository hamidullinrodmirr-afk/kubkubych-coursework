from rest_framework import serializers

from .models import Service
from doctors.serializers import SpecialtySerializer


class ServiceSerializer(serializers.ModelSerializer):
    """Карточка услуги со специализацией и статистикой записей.

    Поля ``total_bookings`` и ``completed_bookings`` заполняются
    аннотациями queryset из ``ServiceViewSet.get_queryset``.
    """

    specialty_detail = SpecialtySerializer(source='specialty', read_only=True)
    total_bookings = serializers.SerializerMethodField()
    completed_bookings = serializers.SerializerMethodField()

    class Meta:
        model = Service
        fields = (
            'id', 'name', 'description', 'price', 'duration_minutes',
            'specialty', 'specialty_detail', 'photo', 'is_active',
            'total_bookings', 'completed_bookings',
        )

    def get_total_bookings(self, obj: Service) -> int:
        """Сколько раз услугу заказывали (аннотация queryset)."""
        return getattr(obj, 'total_bookings', 0)

    def get_completed_bookings(self, obj: Service) -> int:
        """Сколько приёмов по услуге завершено (аннотация queryset)."""
        return getattr(obj, 'completed_bookings', 0)


class ServiceShortSerializer(serializers.ModelSerializer):
    """Краткая карточка услуги для вложенного отображения."""

    class Meta:
        model = Service
        fields = ('id', 'name', 'price', 'duration_minutes')
