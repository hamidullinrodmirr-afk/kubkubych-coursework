from rest_framework import serializers
from .models import Service
from doctors.serializers import SpecialtySerializer


class ServiceSerializer(serializers.ModelSerializer):
    specialty_detail = SpecialtySerializer(source='specialty', read_only=True)

    class Meta:
        model = Service
        fields = (
            'id', 'name', 'description', 'price', 'duration_minutes',
            'specialty', 'specialty_detail', 'photo', 'is_active',
        )


class ServiceShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Service
        fields = ('id', 'name', 'price', 'duration_minutes')
