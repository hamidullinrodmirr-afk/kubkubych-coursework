from django.db.models import Q
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from users.permissions import IsAdmin
from .filters import ReviewFilter
from .models import Review
from .permissions import IsReviewAuthorOrAdmin
from .serializers import ReviewCreateSerializer, ReviewModerationSerializer, ReviewSerializer


class ReviewViewSet(viewsets.ModelViewSet):
    """Отзывы: публичны одобренные, автор правит свой, модерация — админ."""

    filterset_class = ReviewFilter
    ordering_fields = ('created_at', 'rating')

    def get_queryset(self):
        queryset = Review.objects.select_related('author', 'product', 'product__category')
        user = self.request.user
        if user.is_authenticated and user.role == 'admin':
            return queryset
        if user.is_authenticated:
            return queryset.filter(Q(is_approved=True) | Q(author=user))
        return queryset.filter(is_approved=True)

    def get_serializer_class(self):
        if self.action == 'create':
            return ReviewCreateSerializer
        if self.action == 'moderate':
            return ReviewModerationSerializer
        return ReviewSerializer

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [permissions.AllowAny()]
        if self.action == 'moderate':
            return [IsAdmin()]
        if self.action in ('update', 'partial_update', 'destroy'):
            return [permissions.IsAuthenticated(), IsReviewAuthorOrAdmin()]
        return [permissions.IsAuthenticated()]

    def perform_update(self, serializer):
        """После правки покупателем отзыв снова уходит на модерацию."""
        if self.request.user.role == 'admin':
            serializer.save()
        else:
            serializer.save(is_approved=False, moderation_comment='')

    @action(detail=True, methods=('patch',))
    def moderate(self, request, pk=None):
        """Одобрение или отклонение отзыва администратором."""
        review = self.get_object()
        serializer = self.get_serializer(review, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(ReviewSerializer(review).data)
