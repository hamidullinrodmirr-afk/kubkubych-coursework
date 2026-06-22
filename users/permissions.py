from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAdminRole(BasePermission):
    """Доступ только для администратора магазина."""

    def has_permission(self, request, view) -> bool:
        return request.user.is_authenticated and request.user.role == 'admin'


# Совместимое имя, используемое по проекту.
IsAdmin = IsAdminRole


class IsClient(BasePermission):
    """Доступ для авторизованного покупателя."""

    def has_permission(self, request, view) -> bool:
        return request.user.is_authenticated and request.user.role == 'client'


class IsActiveUser(BasePermission):
    """Заблокированный пользователь (is_active=False) теряет доступ к API."""

    def has_permission(self, request, view) -> bool:
        return request.user.is_authenticated and request.user.is_active


class IsOwnerOrAdmin(BasePermission):
    """Доступ к объекту его владельцу либо администратору."""

    def has_object_permission(self, request, view, obj) -> bool:
        user = request.user
        owner_id = getattr(obj, 'user_id', None) or getattr(obj, 'id', None)
        return user.is_authenticated and (owner_id == user.id or user.role == 'admin')


class ReadOnlyOrAdmin(BasePermission):
    """Безопасные методы — всем, изменения — только администратору."""

    def has_permission(self, request, view) -> bool:
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.role == 'admin'
