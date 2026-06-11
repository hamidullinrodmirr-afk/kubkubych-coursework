from rest_framework import serializers

from .models import Pet


class PetSerializer(serializers.ModelSerializer):
    """Питомец текущего пользователя; владелец проставляется автоматически."""

    owner = serializers.HiddenField(default=serializers.CurrentUserDefault())
    species_display = serializers.CharField(source='get_species_display', read_only=True)

    class Meta:
        model = Pet
        fields = (
            'id', 'owner', 'name', 'species', 'species_display',
            'breed', 'age', 'weight', 'health_notes', 'photo', 'created_at',
        )
        read_only_fields = ('id', 'created_at')

    def validate_name(self, value: str) -> str:
        """Кличка может содержать только буквы и пробелы.

        Args:
            value: Проверяемая кличка.

        Returns:
            Кличка без изменений.

        Raises:
            serializers.ValidationError: При недопустимых символах.
        """
        if not all(c.isalpha() or c.isspace() for c in value):
            raise serializers.ValidationError('Кличка может содержать только буквы и пробелы')
        return value


class PetShortSerializer(serializers.ModelSerializer):
    """Краткая карточка питомца для вложенного отображения."""

    class Meta:
        model = Pet
        fields = ('id', 'name', 'species', 'breed')
