from django.db.models import Count
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from users.permissions import IsAdmin
from .filters import OrderFilter
from .models import Order
from .permissions import IsOrderOwnerOrAdmin
from .serializers import (
    OrderCreateSerializer,
    OrderDetailSerializer,
    OrderListSerializer,
    OrderStatusUpdateSerializer,
)
from .services import change_order_status


class OrderViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    viewsets.GenericViewSet,
):
    """Заказы покупателя: оформление, история, отмена; смена статуса — админ."""

    permission_classes = (permissions.IsAuthenticated,)
    filterset_class = OrderFilter
    ordering_fields = ('created_at', 'total', 'status')

    def get_queryset(self):
        queryset = (
            Order.objects.select_related('user')
            .prefetch_related('items__product')
            .annotate(items_count=Count('items'))
            .order_by('-created_at')
        )
        user = self.request.user
        if user.is_authenticated and user.role == 'admin':
            return queryset
        return queryset.filter(user=user)

    def get_serializer_class(self):
        if self.action == 'list':
            return OrderListSerializer
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderDetailSerializer

    def get_permissions(self):
        if self.action in ('retrieve', 'cancel'):
            return [permissions.IsAuthenticated(), IsOrderOwnerOrAdmin()]
        if self.action == 'change_status':
            return [IsAdmin()]
        return [permissions.IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        return Response(OrderDetailSerializer(order).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=('post',))
    def cancel(self, request, pk=None):
        """Отмена заказа покупателем (до отправки) или администратором."""
        order = self.get_object()
        if Order.Status.CANCELLED not in order.ALLOWED_TRANSITIONS.get(order.status, set()):
            return Response(
                {'detail': 'Этот заказ уже нельзя отменить.'}, status=status.HTTP_400_BAD_REQUEST
            )
        change_order_status(order, Order.Status.CANCELLED)
        return Response(OrderDetailSerializer(order).data)

    @action(detail=True, methods=('patch',), url_path='status')
    def change_status(self, request, pk=None):
        """Перевод заказа в новый статус администратором."""
        order = self.get_object()
        serializer = OrderStatusUpdateSerializer(order, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(OrderDetailSerializer(order).data)
