from django.db.models import Q, QuerySet
from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.response import Response

from .models import Review
from .serializers import ReviewSerializer, ReviewListSerializer
from users.permissions import IsAdmin


class ReviewViewSet(viewsets.ModelViewSet):
    """Отзывы: публично видны одобренные, автору — также его собственные.

    Редактирование и удаление доступны автору и администратору; после
    правки автором отзыв снова уходит на модерацию.
    """

    filterset_fields = ['doctor', 'rating', 'is_approved']
    ordering_fields = ['created_at', 'rating']

    def get_queryset(self) -> QuerySet[Review]:
        """Queryset отзывов с учётом роли и авторства."""
        user = self.request.user
        qs = Review.objects.select_related('author', 'doctor__user', 'appointment')
        if user.is_authenticated and user.role == 'admin':
            return qs
        if user.is_authenticated:
            return qs.filter(Q(is_approved=True) | Q(author=user))
        return qs.filter(is_approved=True)

    def get_serializer_class(self) -> type:
        """Сериализатор в зависимости от действия."""
        if self.action == 'list':
            return ReviewListSerializer
        return ReviewSerializer

    def get_permissions(self) -> list[BasePermission]:
        """Права доступа: чтение — всем, одобрение — администратору."""
        if self.action in ('list', 'retrieve'):
            return [permissions.AllowAny()]
        if self.action == 'approve':
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def perform_update(self, serializer: ReviewSerializer) -> None:
        """Сохраняет правку отзыва с проверкой авторства.

        Отзыв, отредактированный не администратором, снимается с публикации
        до повторной модерации.

        Args:
            serializer: Валидированный сериализатор отзыва.

        Raises:
            PermissionDenied: Если чужой отзыв правит не администратор.
        """
        user = self.request.user
        if user.role != 'admin' and serializer.instance.author_id != user.id:
            raise PermissionDenied('Вы можете редактировать только свои отзывы')
        if user.role == 'admin':
            serializer.save()
        else:
            serializer.save(is_approved=False)

    def perform_destroy(self, instance: Review) -> None:
        """Удаляет отзыв с проверкой авторства.

        Args:
            instance: Удаляемый отзыв.

        Raises:
            PermissionDenied: Если чужой отзыв удаляет не администратор.
        """
        user = self.request.user
        if user.role != 'admin' and instance.author != user:
            raise PermissionDenied('Вы можете удалять только свои отзывы')
        instance.delete()

    @action(detail=True, methods=['post'])
    def approve(self, request: Request, pk: int | None = None) -> Response:
        """Одобрение отзыва администратором (модерация).

        Args:
            request: HTTP-запрос.
            pk: Идентификатор отзыва.

        Returns:
            Сериализованный одобренный отзыв.
        """
        review = self.get_object()
        review.is_approved = True
        review.save()
        return Response(ReviewSerializer(review, context=self.get_serializer_context()).data)
