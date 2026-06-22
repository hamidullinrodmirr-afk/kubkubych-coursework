from typing import Any

from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .filters import UserFilter
from .permissions import IsActiveUser, IsAdmin, IsOwnerOrAdmin
from .serializers import (
    AdminUserSerializer,
    LogoutSerializer,
    UserListSerializer,
    UserProfileSerializer,
    UserRegistrationSerializer,
    UserRoleSerializer,
)

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """Регистрация нового клиента."""

    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserProfileSerializer(user).data, status=status.HTTP_201_CREATED)


class ProfileView(generics.RetrieveUpdateAPIView):
    """Просмотр и редактирование профиля текущего пользователя."""

    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsActiveUser]

    def get_object(self) -> Any:
        return self.request.user


class LogoutView(APIView):
    """Выход: отзыв refresh-токена через blacklist."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request: Request) -> Response:
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            RefreshToken(serializer.validated_data['refresh']).blacklist()
        except TokenError:
            return Response({'detail': 'Некорректный или просроченный токен.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_205_RESET_CONTENT)


class UserListView(generics.ListAPIView):
    """Список пользователей для администратора с фильтрами и поиском."""

    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserListSerializer
    permission_classes = [IsAdmin]
    filterset_class = UserFilter


class UserDetailView(generics.RetrieveUpdateAPIView):
    """Карточка пользователя: администратору — полная, владельцу — профиль."""

    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated, IsOwnerOrAdmin]

    def get_serializer_class(self):
        return AdminUserSerializer if self.request.user.role == 'admin' else UserProfileSerializer


class UserRoleView(generics.UpdateAPIView):
    """Назначение роли пользователю администратором."""

    queryset = User.objects.all()
    serializer_class = UserRoleSerializer
    permission_classes = [IsAdmin]


class _BlockStateView(generics.UpdateAPIView):
    """Базовый класс блокировки и разблокировки покупателя."""

    queryset = User.objects.all()
    serializer_class = UserListSerializer
    permission_classes = [IsAdmin]
    target_active: bool = True

    def patch(self, request: Request, *args: Any, **kwargs: Any) -> Response:
        user = self.get_object()
        if user == request.user:
            return Response(
                {'detail': 'Нельзя менять статус собственной учётной записи.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.is_active = self.target_active
        user.save(update_fields=('is_active', 'updated_at'))
        return Response(self.get_serializer(user).data)


class UserBlockView(_BlockStateView):
    """Блокировка покупателя (is_active=False)."""

    target_active = False


class UserUnblockView(_BlockStateView):
    """Разблокировка покупателя (is_active=True)."""

    target_active = True
