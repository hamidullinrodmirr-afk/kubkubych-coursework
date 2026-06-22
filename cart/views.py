from decimal import Decimal
from rest_framework import mixins, permissions, viewsets
from rest_framework.response import Response

from .models import CartItem
from .serializers import CartItemSerializer


class CartItemViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    serializer_class = CartItemSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return CartItem.objects.filter(user=self.request.user).select_related('product__category')

    def list(self, request, *args, **kwargs):
        items = self.get_queryset()
        return Response({'items': self.get_serializer(items, many=True).data, 'total': sum((item.product.final_price * item.quantity for item in items), Decimal('0.00'))})
