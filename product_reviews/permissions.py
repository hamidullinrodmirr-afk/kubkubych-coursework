from rest_framework.permissions import BasePermission


class IsReviewAuthorOrAdmin(BasePermission):
    """Редактировать и удалять отзыв может его автор либо администратор."""

    def has_object_permission(self, request, view, obj) -> bool:
        user = request.user
        return user.is_authenticated and (obj.author_id == user.id or user.role == 'admin')
