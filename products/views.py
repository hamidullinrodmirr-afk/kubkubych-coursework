from django.db.models import Avg, Count, Prefetch, Q, Sum
from django.db.models.functions import Coalesce
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from orders.models import Order
from product_reviews.models import Review
from users.permissions import IsAdmin
from .constants import POPULAR_PRODUCTS_LIMIT
from .filters import ProductFilter
from .models import Category, Favorite, Product
from .serializers import (
    CategorySerializer,
    FavoriteSerializer,
    ProductCreateUpdateSerializer,
    ProductDetailSerializer,
    ProductListSerializer,
)


class CategoryViewSet(viewsets.ModelViewSet):
    """Серии конструкторов: публичный просмотр активных, управление — админ."""

    serializer_class = CategorySerializer

    def get_queryset(self):
        queryset = Category.objects.all()
        if not self._is_admin():
            queryset = queryset.filter(is_active=True)
        return queryset

    def get_permissions(self):
        return [permissions.AllowAny()] if self.action in ('list', 'retrieve') else [IsAdmin()]

    def _is_admin(self) -> bool:
        user = self.request.user
        return user.is_authenticated and user.role == 'admin'


class ProductViewSet(viewsets.ModelViewSet):
    """Каталог наборов с аннотациями, фильтрами и действиями избранного."""

    filterset_class = ProductFilter
    ordering_fields = (
        'price', 'name', 'pieces', 'created_at',
        'average_rating', 'sold_units', 'favorites_count',
    )
    ordering = ('name',)
    lookup_field = 'pk'

    def get_queryset(self):
        queryset = (
            Product.objects.select_related('category')
            .annotate(
                average_rating=Avg('reviews__rating', filter=Q(reviews__is_approved=True)),
                reviews_count=Count('reviews', filter=Q(reviews__is_approved=True), distinct=True),
                favorites_count=Count('favorited_by', distinct=True),
                sold_units=Coalesce(
                    Sum('order_items__quantity', filter=Q(order_items__order__status=Order.Status.DELIVERED)),
                    0,
                ),
            )
        )
        if not self._is_admin():
            queryset = queryset.filter(is_active=True)
        if self.action == 'retrieve':
            queryset = queryset.prefetch_related(
                Prefetch(
                    'reviews',
                    queryset=Review.objects.filter(is_approved=True).select_related('author'),
                    to_attr='approved_reviews',
                )
            )
        return queryset

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return ProductCreateUpdateSerializer
        if self.action == 'retrieve':
            return ProductDetailSerializer
        return ProductListSerializer

    def get_permissions(self):
        if self.action in ('list', 'retrieve', 'popular', 'discounts'):
            return [permissions.AllowAny()]
        if self.action in ('favorite', 'favorites'):
            return [permissions.IsAuthenticated()]
        return [IsAdmin()]

    def get_serializer_context(self):
        """Прокидывает набор id избранного, чтобы is_favorite не делал N+1."""
        context = super().get_serializer_context()
        user = self.request.user
        if user.is_authenticated:
            context['favorite_product_ids'] = set(
                Favorite.objects.filter(user=user).values_list('product_id', flat=True)
            )
        else:
            context['favorite_product_ids'] = set()
        return context

    def _is_admin(self) -> bool:
        user = self.request.user
        return user.is_authenticated and user.role == 'admin'

    @action(detail=True, methods=('post', 'delete'))
    def favorite(self, request, pk=None):
        """Добавляет или убирает набор из избранного текущего покупателя."""
        product = self.get_object()
        if request.method == 'DELETE':
            Favorite.objects.filter(user=request.user, product=product).delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        if not product.is_active:
            return Response(
                {'detail': 'Нельзя добавить в избранное недоступный набор.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        favorite, created = Favorite.objects.get_or_create(user=request.user, product=product)
        serializer = FavoriteSerializer(favorite, context=self.get_serializer_context())
        return Response(serializer.data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    @action(detail=False, methods=('get',))
    def favorites(self, request):
        """Список наборов в избранном текущего покупателя."""
        queryset = self.filter_queryset(self.get_queryset()).filter(favorited_by__user=request.user)
        serializer = ProductListSerializer(queryset, many=True, context=self.get_serializer_context())
        return Response(serializer.data)

    @action(detail=False, methods=('get',))
    def popular(self, request):
        """Подборка самых продаваемых наборов."""
        queryset = self.get_queryset().order_by('-sold_units', '-favorites_count')[:POPULAR_PRODUCTS_LIMIT]
        serializer = ProductListSerializer(queryset, many=True, context=self.get_serializer_context())
        return Response(serializer.data)

    @action(detail=False, methods=('get',))
    def discounts(self, request):
        """Подборка наборов со скидкой."""
        queryset = (
            self.get_queryset().filter(discount_percent__gt=0).order_by('-discount_percent')[:POPULAR_PRODUCTS_LIMIT]
        )
        serializer = ProductListSerializer(queryset, many=True, context=self.get_serializer_context())
        return Response(serializer.data)
