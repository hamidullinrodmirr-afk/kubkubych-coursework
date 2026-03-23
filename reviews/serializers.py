from rest_framework import serializers
from .models import Review
from appointments.models import Appointment


class ReviewSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.full_name', read_only=True)
    doctor_name = serializers.CharField(source='doctor.user.full_name', read_only=True)

    class Meta:
        model = Review
        fields = (
            'id', 'author', 'author_name', 'doctor', 'doctor_name',
            'appointment', 'rating', 'text', 'is_approved',
            'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'author', 'is_approved', 'created_at', 'updated_at')

    def validate_text(self, value):
        if len(value) < 10:
            raise serializers.ValidationError('Отзыв должен содержать не менее 10 символов')
        return value

    def validate(self, attrs):
        request = self.context['request']
        doctor = attrs['doctor']
        appointment = attrs['appointment']

        # Проверка: приём завершён
        if appointment.status != Appointment.Status.COMPLETED:
            raise serializers.ValidationError(
                {'appointment': 'Отзыв можно оставить только после завершённого приёма'}
            )

        # Проверка: приём принадлежит текущему пользователю
        if appointment.client != request.user:
            raise serializers.ValidationError(
                {'appointment': 'Это не ваш приём'}
            )

        # Проверка: приём у этого врача
        if appointment.doctor != doctor:
            raise serializers.ValidationError(
                {'doctor': 'Приём был у другого врача'}
            )

        # Проверка: один отзыв на приём
        if Review.objects.filter(appointment=appointment).exists():
            raise serializers.ValidationError(
                {'appointment': 'Вы уже оставили отзыв на этот приём'}
            )

        return attrs

    def create(self, validated_data):
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)


class ReviewListSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.full_name', read_only=True)

    class Meta:
        model = Review
        fields = ('id', 'author_name', 'rating', 'text', 'created_at')
