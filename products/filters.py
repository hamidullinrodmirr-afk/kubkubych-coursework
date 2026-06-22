import django_filters

from .models import Product


class ProductFilter(django_filters.FilterSet):
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    min_age = django_filters.NumberFilter(field_name='age_max', lookup_expr='gte')
    max_age = django_filters.NumberFilter(field_name='age_min', lookup_expr='lte')
    in_stock = django_filters.BooleanFilter(method='filter_in_stock')
    sale = django_filters.BooleanFilter(method='filter_sale')

    class Meta:
        model = Product
        fields = ('category',)

    def filter_in_stock(self, queryset, _, value):
        return queryset.filter(stock__gt=0) if value else queryset

    def filter_sale(self, queryset, _, value):
        return queryset.filter(discount_percent__gt=0) if value else queryset
