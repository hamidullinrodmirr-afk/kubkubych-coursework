import django_filters

from .models import Doctor


class DoctorFilter(django_filters.FilterSet):
    """Фильтр каталога врачей.

    Поддерживает фильтрацию по специализации (название/идентификатор),
    диапазону стоимости консультации, минимальному стажу и минимальному
    рейтингу (по аннотированному полю ``_avg_rating`` из ``get_queryset``).
    """

    specialty = django_filters.CharFilter(
        field_name='specialties__name',
        lookup_expr='icontains',
        distinct=True,
    )
    specialty_id = django_filters.NumberFilter(
        field_name='specialties__id',
        distinct=True,
    )
    min_price = django_filters.NumberFilter(
        field_name='consultation_price',
        lookup_expr='gte',
    )
    max_price = django_filters.NumberFilter(
        field_name='consultation_price',
        lookup_expr='lte',
    )
    min_experience = django_filters.NumberFilter(
        field_name='experience_years',
        lookup_expr='gte',
    )
    min_rating = django_filters.NumberFilter(
        field_name='_avg_rating',
        lookup_expr='gte',
    )

    class Meta:
        model = Doctor
        fields = ('is_available',)
