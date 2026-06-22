from rest_framework.permissions import BasePermission


class IsCartItemOwner(BasePermission):
    """Позволяет менять позицию корзины только её владельцу."""

    def has_object_permission(self, request, view, obj) -> bool:
        return obj.user_id == request.user.id
