from decimal import Decimal

from rest_framework import mixins, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import CartItem
from .permissions import IsCartItemOwner
from .serializers import CartItemCreateSerializer, CartItemSerializer, CartSummarySerializer


class CartItemViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """CRUD по позициям корзины текущего покупателя."""

    permission_classes = (permissions.IsAuthenticated, IsCartItemOwner)
    pagination_class = None

    def get_queryset(self):
        return CartItem.objects.filter(user=self.request.user).select_related(
            'product', 'product__category', 'user'
        )

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return CartItemCreateSerializer
        return CartItemSerializer


def _cart_summary(user) -> dict:
    """Считает свод по корзине покупателя одним проходом."""
    items = list(CartItem.objects.filter(user=user).select_related('product'))
    total = sum((item.line_total for item in items), Decimal('0.00'))
    total_quantity = sum(item.quantity for item in items)
    return {'total_positions': len(items), 'total_quantity': total_quantity, 'total': total}


class CartSummaryView(APIView):
    """Свод по корзине: позиции, единицы, сумма."""

    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        return Response(CartSummarySerializer(_cart_summary(request.user)).data)


class CartClearView(APIView):
    """Полная очистка корзины покупателя."""

    permission_classes = (permissions.IsAuthenticated,)

    def delete(self, request):
        CartItem.objects.filter(user=request.user).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
