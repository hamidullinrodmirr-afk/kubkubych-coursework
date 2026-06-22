import django_filters

from .models import Review


class ReviewFilter(django_filters.FilterSet):
    """Фильтры отзывов: набор, автор, оценка, статус модерации."""

    class Meta:
        model = Review
        fields = ('product', 'author', 'rating', 'is_approved')
