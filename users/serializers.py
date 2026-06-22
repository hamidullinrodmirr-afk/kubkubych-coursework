from typing import Any

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Регистрация клиента: пара паролей и проверка стойкости пароля."""

    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'phone', 'password', 'password_confirm')

    def validate(self, attrs: dict[str, Any]) -> dict[str, Any]:
        """Проверяет совпадение паролей и их стойкость по валидаторам Django."""
        if attrs['password'] != attrs.pop('password_confirm'):
            raise serializers.ValidationError({'password_confirm': 'Пароли не совпадают'})

        probe = User(
            email=attrs.get('email', ''),
            first_name=attrs.get('first_name', ''),
            last_name=attrs.get('last_name', ''),
        )
        try:
            validate_password(attrs['password'], probe)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({'password': list(exc.messages)})
        return attrs

    def create(self, validated_data: dict[str, Any]) -> Any:
        """Создаёт пользователя через менеджер (хеширование пароля)."""
        return User.objects.create_user(**validated_data)


class UserProfileSerializer(serializers.ModelSerializer):
    """Профиль текущего пользователя; роль и email менять нельзя."""

    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'full_name', 'phone', 'role', 'avatar', 'date_joined')
        read_only_fields = ('id', 'email', 'role', 'date_joined')


class UserListSerializer(serializers.ModelSerializer):
    """Краткая карточка пользователя для списка в админ-API."""

    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'phone', 'role', 'is_active')


class AdminUserSerializer(serializers.ModelSerializer):
    """Полная карточка пользователя для администратора."""

    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = (
            'id', 'email', 'first_name', 'last_name', 'full_name', 'phone',
            'role', 'is_active', 'is_staff', 'date_joined', 'updated_at',
        )
        read_only_fields = ('id', 'email', 'is_staff', 'date_joined', 'updated_at')


class UserRoleSerializer(serializers.ModelSerializer):
    """Назначение роли пользователю администратором."""

    class Meta:
        model = User
        fields = ('id', 'role')
        read_only_fields = ('id',)


class LogoutSerializer(serializers.Serializer):
    """Отзыв refresh-токена при выходе."""

    refresh = serializers.CharField()
