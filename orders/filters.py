import django_filters

from .models import Order


class OrderFilter(django_filters.FilterSet):
    """Фильтры списка заказов: статус, период и сумма."""

    status = django_filters.ChoiceFilter(choices=Order.Status.choices)
    date_from = django_filters.DateFilter(field_name='created_at', lookup_expr='date__gte')
    date_to = django_filters.DateFilter(field_name='created_at', lookup_expr='date__lte')
    min_total = django_filters.NumberFilter(field_name='total', lookup_expr='gte')
    max_total = django_filters.NumberFilter(field_name='total', lookup_expr='lte')

    class Meta:
        model = Order
        fields = ('status',)
