from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.views import APIView


class IsAdmin(BasePermission):
    """Доступ только для администраторов."""

    def has_permission(self, request: Request, view: APIView) -> bool:
        """Проверяет, что пользователь аутентифицирован и имеет роль admin."""
        return request.user.is_authenticated and request.user.role == 'admin'


class IsVeterinarian(BasePermission):
    """Доступ только для ветеринаров."""

    def has_permission(self, request: Request, view: APIView) -> bool:
        """Проверяет, что пользователь аутентифицирован и имеет роль veterinarian."""
        return request.user.is_authenticated and request.user.role == 'veterinarian'


class IsClient(BasePermission):
    """Доступ только для клиентов."""

    def has_permission(self, request: Request, view: APIView) -> bool:
        """Проверяет, что пользователь аутентифицирован и имеет роль client."""
        return request.user.is_authenticated and request.user.role == 'client'


class IsAdminOrOwnDoctorProfile(BasePermission):
    """Администратор — любой профиль врача, ветеринар — только свой."""

    def has_permission(self, request: Request, view: APIView) -> bool:
        """Пропускает только администраторов и ветеринаров."""
        return request.user.is_authenticated and request.user.role in ('admin', 'veterinarian')

    def has_object_permission(self, request: Request, view: APIView, obj) -> bool:
        """Администратору доступен любой объект, врачу — только его профиль.

        Args:
            request: HTTP-запрос.
            view: Обрабатывающее представление.
            obj: Проверяемый профиль врача.

        Returns:
            True, если доступ разрешён.
        """
        if request.user.role == 'admin':
            return True
        return obj.user_id == request.user.id
