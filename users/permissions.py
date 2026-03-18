from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'


class IsVeterinarian(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'veterinarian'


class IsClient(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'client'
