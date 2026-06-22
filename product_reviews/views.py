from django.db.models import Q
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from users.permissions import IsAdmin
from .models import Review
from .serializers import ReviewSerializer

class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    filterset_fields = ('product', 'rating', 'is_approved')
    ordering_fields = ('created_at', 'rating')
    def get_queryset(self):
        qs = Review.objects.select_related('author', 'product')
        user = self.request.user
        if user.is_authenticated and user.role == 'admin': return qs
        return qs.filter(Q(is_approved=True) | Q(author=user)) if user.is_authenticated else qs.filter(is_approved=True)
    def get_permissions(self):
        if self.action in ('list', 'retrieve'): return (permissions.AllowAny(),)
        if self.action == 'moderate': return (IsAdmin(),)
        return (permissions.IsAuthenticated(),)
    def perform_update(self, serializer):
        if self.request.user.role != 'admin' and serializer.instance.author_id != self.request.user.id: raise PermissionDenied('Можно редактировать только собственный отзыв.')
        serializer.save(is_approved=self.request.user.role == 'admin')
    def perform_destroy(self, instance):
        if self.request.user.role != 'admin' and instance.author_id != self.request.user.id: raise PermissionDenied('Можно удалить только собственный отзыв.')
        instance.delete()
    @action(detail=True, methods=('patch',), permission_classes=(IsAdmin,))
    def moderate(self, request, pk=None):
        review = self.get_object(); review.is_approved = bool(request.data.get('is_approved', True)); review.save(update_fields=('is_approved', 'updated_at'))
        return Response(self.get_serializer(review).data)
