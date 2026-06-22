from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """Доступ только для администратора магазина."""

    def has_permission(self, request, view) -> bool:
        return request.user.is_authenticated and request.user.role == 'admin'


class IsClient(BasePermission):
    """Доступ для авторизованного покупателя."""

    def has_permission(self, request, view) -> bool:
        return request.user.is_authenticated and request.user.role == 'client'
