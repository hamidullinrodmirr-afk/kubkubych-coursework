from typing import Any

from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.request import Request
from rest_framework.response import Response

from .serializers import UserRegistrationSerializer, UserProfileSerializer, UserListSerializer
from .permissions import IsAdmin

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """Регистрация нового клиента."""

    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        """Создаёт пользователя и возвращает его профиль.

        Args:
            request: HTTP-запрос с данными регистрации.

        Returns:
            Профиль созданного пользователя со статусом 201.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            UserProfileSerializer(user).data,
            status=status.HTTP_201_CREATED,
        )


class ProfileView(generics.RetrieveUpdateAPIView):
    """Просмотр и редактирование профиля текущего пользователя."""

    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self) -> Any:
        """Возвращает текущего аутентифицированного пользователя."""
        return self.request.user


class UserListView(generics.ListAPIView):
    """Список пользователей для администратора с фильтрацией и поиском."""

    queryset = User.objects.all()
    serializer_class = UserListSerializer
    permission_classes = [IsAdmin]
    filterset_fields = ['role', 'is_active']
    search_fields = ['email', 'first_name', 'last_name']
