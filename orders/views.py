from rest_framework import mixins, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from users.permissions import IsAdmin
from .models import Order
from .serializers import OrderSerializer, OrderStatusSerializer


class OrderViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = OrderSerializer
    permission_classes = (permissions.IsAuthenticated,)
    filterset_fields = ('status',)

    def get_queryset(self):
        qs = Order.objects.select_related('user').prefetch_related('items__product')
        return qs if self.request.user.role == 'admin' else qs.filter(user=self.request.user)

    @action(detail=True, methods=('patch',), permission_classes=(IsAdmin,), url_path='status')
    def change_status(self, request, pk=None):
        serializer = OrderStatusSerializer(self.get_object(), data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(OrderSerializer(serializer.instance).data)
