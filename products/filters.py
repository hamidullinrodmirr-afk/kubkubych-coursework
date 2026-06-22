import django_filters
from django.db.models import Q, QuerySet

from .models import Product


class ProductFilter(django_filters.FilterSet):
    """Фильтры каталога: серия, цена, возраст, детали, наличие, скидка, рейтинг."""

    category = django_filters.NumberFilter(field_name='category_id')
    category_slug = django_filters.CharFilter(field_name='category__slug')
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    age_from = django_filters.NumberFilter(field_name='age_from', lookup_expr='gte')
    age_to = django_filters.NumberFilter(field_name='age_to', lookup_expr='lte')
    min_pieces = django_filters.NumberFilter(field_name='pieces', lookup_expr='gte')
    max_pieces = django_filters.NumberFilter(field_name='pieces', lookup_expr='lte')
    in_stock = django_filters.BooleanFilter(method='filter_in_stock')
    has_discount = django_filters.BooleanFilter(method='filter_has_discount')
    min_rating = django_filters.NumberFilter(method='filter_min_rating')
    search = django_filters.CharFilter(method='filter_search')

    class Meta:
        model = Product
        fields = ('category', 'category_slug')

    def filter_in_stock(self, queryset: QuerySet, _name: str, value: bool) -> QuerySet:
        return queryset.filter(stock__gt=0) if value else queryset

    def filter_has_discount(self, queryset: QuerySet, _name: str, value: bool) -> QuerySet:
        return queryset.filter(discount_percent__gt=0) if value else queryset

    def filter_min_rating(self, queryset: QuerySet, _name: str, value) -> QuerySet:
        # average_rating приходит из annotate() в ProductViewSet.get_queryset().
        return queryset.filter(average_rating__gte=value)

    def filter_search(self, queryset: QuerySet, _name: str, value: str) -> QuerySet:
        return queryset.filter(
            Q(name__icontains=value) | Q(article__icontains=value) | Q(description__icontains=value)
        )
