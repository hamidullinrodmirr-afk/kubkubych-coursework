import django_filters
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()


class UserFilter(django_filters.FilterSet):
    """Фильтры списка пользователей для администратора."""

    search = django_filters.CharFilter(method='filter_search')

    class Meta:
        model = User
        fields = ('role', 'is_active')

    def filter_search(self, queryset, _name, value):
        return queryset.filter(
            Q(email__icontains=value)
            | Q(first_name__icontains=value)
            | Q(last_name__icontains=value)
            | Q(phone__icontains=value)
        )
