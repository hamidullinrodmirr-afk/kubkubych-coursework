from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from .models import Review
from .serializers import ReviewSerializer, ReviewListSerializer
from users.permissions import IsAdmin


class ReviewViewSet(viewsets.ModelViewSet):
    filterset_fields = ['doctor', 'rating', 'is_approved']
    ordering_fields = ['created_at', 'rating']

    def get_queryset(self):
        user = self.request.user
        if user.is_authenticated and user.role == 'admin':
            return Review.objects.select_related('author', 'doctor__user', 'appointment')
        return Review.objects.filter(is_approved=True).select_related('author', 'doctor__user')

    def get_serializer_class(self):
        if self.action == 'list':
            return ReviewListSerializer
        return ReviewSerializer

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [permissions.AllowAny()]
        if self.action == 'approve':
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def perform_destroy(self, instance):
        user = self.request.user
        if user.role != 'admin' and instance.author != user:
            raise PermissionDenied('Вы можете удалять только свои отзывы')
        instance.delete()

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        review = self.get_object()
        review.is_approved = True
        review.save()
        return Response(ReviewSerializer(review).data)
