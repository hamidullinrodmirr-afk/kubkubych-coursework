import django_filters

from .models import Service


class ServiceFilter(django_filters.FilterSet):
    """Фильтр каталога услуг: специализация, цена, длительность, название."""

    name = django_filters.CharFilter(lookup_expr='icontains')
    min_price = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    max_duration = django_filters.NumberFilter(field_name='duration_minutes', lookup_expr='lte')

    class Meta:
        model = Service
        fields = ('specialty', 'is_active')
