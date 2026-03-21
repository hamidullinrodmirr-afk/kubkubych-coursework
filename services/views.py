from rest_framework import viewsets, permissions
from .models import Service
from .serializers import ServiceSerializer
from users.permissions import IsAdmin


class ServiceViewSet(viewsets.ModelViewSet):
    queryset = Service.objects.select_related('specialty').filter(is_active=True)
    serializer_class = ServiceSerializer
    filterset_fields = ['specialty', 'is_active']
    search_fields = ['name']
    ordering_fields = ['price', 'name']

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [permissions.AllowAny()]
        return [IsAdmin()]
