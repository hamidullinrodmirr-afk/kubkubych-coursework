from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from users.permissions import IsAdmin
from .filters import ProductFilter
from .models import Category, Favorite, Product
from .serializers import CategorySerializer, ProductSerializer


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_permissions(self):
        return [permissions.AllowAny()] if self.action in ('list', 'retrieve') else [IsAdmin()]


class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    filterset_class = ProductFilter
    search_fields = ('name', 'article', 'description')
    ordering_fields = ('price', 'name', 'pieces', 'stock')

    def get_queryset(self):
        queryset = Product.objects.select_related('category').all()
        if not (self.request.user.is_authenticated and self.request.user.role == 'admin'):
            queryset = queryset.filter(is_active=True)
        return queryset

    def get_permissions(self):
        return [permissions.AllowAny()] if self.action in ('list', 'retrieve') else [IsAdmin()]

    @action(detail=True, methods=('post', 'delete'), permission_classes=(permissions.IsAuthenticated,))
    def favorite(self, request, pk=None):
        product = self.get_object()
        if request.method == 'DELETE':
            Favorite.objects.filter(user=request.user, product=product).delete()
            return Response(status=204)
        favorite, created = Favorite.objects.get_or_create(user=request.user, product=product)
        return Response({'product': product.id, 'is_favorite': True}, status=201 if created else 200)
