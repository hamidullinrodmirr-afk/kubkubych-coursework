from django.db.models import Count, Q, QuerySet
from rest_framework import viewsets, permissions
from rest_framework.permissions import BasePermission

from .filters import ServiceFilter
from .models import Service
from .serializers import ServiceSerializer
from appointments.models import Appointment
from users.permissions import IsAdmin


class ServiceViewSet(viewsets.ModelViewSet):
    """Каталог услуг: клиентам видны активные, администратору — все."""

    serializer_class = ServiceSerializer
    filterset_class = ServiceFilter
    search_fields = ['name']
    ordering_fields = ['price', 'name']

    def get_queryset(self) -> QuerySet[Service]:
        """Queryset услуг с аннотациями популярности.

        Returns:
            Queryset с ``select_related('specialty')`` и аннотациями
            ``total_bookings`` (все записи) и ``completed_bookings``
            (завершённые приёмы); для не-администраторов — только активные.
        """
        qs = Service.objects.select_related('specialty').annotate(
            total_bookings=Count('appointments'),
            completed_bookings=Count(
                'appointments',
                filter=Q(appointments__status=Appointment.Status.COMPLETED),
            ),
        ).order_by('specialty', 'name')
        user = self.request.user
        if user.is_authenticated and user.role == 'admin':
            return qs
        return qs.filter(is_active=True)

    def get_permissions(self) -> list[BasePermission]:
        """Права доступа: чтение — всем, изменение — администратору."""
        if self.action in ('list', 'retrieve'):
            return [permissions.AllowAny()]
        return [IsAdmin()]
