from typing import Any

from rest_framework import serializers

from .models import Review
from appointments.models import Appointment


class ReviewSerializer(serializers.ModelSerializer):
    """Создание и редактирование отзыва о враче.

    Отзыв допускается только по собственному завершённому приёму
    у этого врача; на один приём — один отзыв.
    """

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

    def validate_text(self, value: str) -> str:
        """Минимальная длина текста отзыва — 10 символов.

        Args:
            value: Текст отзыва.

        Returns:
            Текст без изменений.

        Raises:
            serializers.ValidationError: Если текст короче 10 символов.
        """
        if len(value) < 10:
            raise serializers.ValidationError('Отзыв должен содержать не менее 10 символов')
        return value

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Сквозная валидация отзыва по бизнес-правилам.

        При частичном обновлении недостающие связи берутся из
        редактируемого объекта.

        Args:
            attrs: Данные сериализатора.

        Returns:
            Проверенные данные.

        Raises:
            serializers.ValidationError: При нарушении любого правила.
        """
        request = self.context['request']
        doctor = attrs.get('doctor') or (self.instance.doctor if self.instance else None)
        appointment = attrs.get('appointment') or (
            self.instance.appointment if self.instance else None
        )
        if doctor is None or appointment is None:
            raise serializers.ValidationError('Укажите врача и приём')

        if appointment.status != Appointment.Status.COMPLETED:
            raise serializers.ValidationError(
                {'appointment': 'Отзыв можно оставить только после завершённого приёма'}
            )

        author = self.instance.author if self.instance else request.user
        if appointment.client != author:
            raise serializers.ValidationError(
                {'appointment': 'Это не ваш приём'}
            )

        if appointment.doctor != doctor:
            raise serializers.ValidationError(
                {'doctor': 'Приём был у другого врача'}
            )

        duplicates = Review.objects.filter(appointment=appointment)
        if self.instance:
            duplicates = duplicates.exclude(pk=self.instance.pk)
        if duplicates.exists():
            raise serializers.ValidationError(
                {'appointment': 'Вы уже оставили отзыв на этот приём'}
            )

        return attrs

    def create(self, validated_data: dict[str, Any]) -> Review:
        """Создаёт отзыв от имени текущего пользователя.

        Args:
            validated_data: Проверенные данные сериализатора.

        Returns:
            Созданный отзыв.
        """
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)


class ReviewListSerializer(serializers.ModelSerializer):
    """Краткая карточка отзыва для публичных списков."""

    author_name = serializers.CharField(source='author.full_name', read_only=True)

    class Meta:
        model = Review
        fields = ('id', 'author_name', 'rating', 'text', 'created_at')
