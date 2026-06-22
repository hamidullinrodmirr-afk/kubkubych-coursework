from rest_framework.permissions import BasePermission


class IsOrderOwnerOrAdmin(BasePermission):
    """Доступ к заказу — его владельцу либо администратору."""

    def has_object_permission(self, request, view, obj) -> bool:
        user = request.user
        return user.is_authenticated and (obj.user_id == user.id or user.role == 'admin')
