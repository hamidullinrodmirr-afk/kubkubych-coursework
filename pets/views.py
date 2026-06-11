from django.db.models import QuerySet
from rest_framework import viewsets, permissions

from .models import Pet
from .serializers import PetSerializer


class PetViewSet(viewsets.ModelViewSet):
    """CRUD питомцев: каждый клиент работает только со своими."""

    serializer_class = PetSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet[Pet]:
        """Queryset питомцев текущего пользователя."""
        return Pet.objects.filter(owner=self.request.user).select_related('owner')
