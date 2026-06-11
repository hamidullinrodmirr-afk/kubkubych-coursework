import django_filters

from .models import Appointment


class AppointmentFilter(django_filters.FilterSet):
    """Фильтр записей на приём: статус, врач, дата и диапазон дат."""

    date_from = django_filters.DateFilter(field_name='date', lookup_expr='gte')
    date_to = django_filters.DateFilter(field_name='date', lookup_expr='lte')

    class Meta:
        model = Appointment
        fields = ('status', 'date', 'doctor')
