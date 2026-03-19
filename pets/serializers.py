from rest_framework import serializers
from .models import Pet


class PetSerializer(serializers.ModelSerializer):
    owner = serializers.HiddenField(default=serializers.CurrentUserDefault())
    species_display = serializers.CharField(source='get_species_display', read_only=True)

    class Meta:
        model = Pet
        fields = (
            'id', 'owner', 'name', 'species', 'species_display',
            'breed', 'age', 'weight', 'health_notes', 'photo', 'created_at',
        )
        read_only_fields = ('id', 'created_at')

    def validate_name(self, value):
        if not all(c.isalpha() or c.isspace() for c in value):
            raise serializers.ValidationError('Кличка может содержать только буквы и пробелы')
        return value


class PetShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pet
        fields = ('id', 'name', 'species', 'breed')
