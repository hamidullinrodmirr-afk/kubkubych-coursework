"""Аналитика магазина на агрегатах ORM — без Python-циклов по выборкам."""

from datetime import timedelta

from django.db.models import Avg, Count, DecimalField, F, Q, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone

from orders.models import Order, OrderItem
from products.constants import LOW_STOCK_THRESHOLD
from products.models import Product
from users.models import User

NEW_USERS_PERIOD_DAYS = 30
TOP_LIMIT = 10


def sales_report() -> dict:
    """Сводка продаж: заказы, выручка, средний чек, разбивка по статусам."""
    orders = Order.objects.all()
    delivered = orders.filter(status=Order.Status.DELIVERED)
    aggregates = delivered.aggregate(
        revenue=Coalesce(Sum('total'), 0, output_field=DecimalField()),
        average_check=Coalesce(Avg('total'), 0, output_field=DecimalField()),
    )
    by_status = orders.values('status').annotate(count=Count('id')).order_by()
    return {
        'total_orders': orders.count(),
        'delivered_orders': delivered.count(),
        'revenue': aggregates['revenue'],
        'average_check': aggregates['average_check'],
        'orders_by_status': {row['status']: row['count'] for row in by_status},
    }


def products_report(limit: int = TOP_LIMIT) -> dict:
    """Популярность наборов: продажи, рейтинг, избранное."""
    top_selling = list(
        OrderItem.objects.filter(order__status=Order.Status.DELIVERED)
        .values('product_id', 'product_name')
        .annotate(
            sold_units=Sum('quantity'),
            revenue=Sum(F('unit_price') * F('quantity'), output_field=DecimalField()),
        )
        .order_by('-sold_units')[:limit]
    )
    top_rated = list(
        Product.objects.annotate(
            average_rating=Avg('reviews__rating', filter=Q(reviews__is_approved=True)),
            reviews_count=Count('reviews', filter=Q(reviews__is_approved=True), distinct=True),
        )
        .filter(reviews_count__gt=0)
        .order_by('-average_rating')[:limit]
        .values('id', 'name', 'average_rating', 'reviews_count')
    )
    most_favorited = list(
        Product.objects.annotate(favorites_count=Count('favorited_by'))
        .filter(favorites_count__gt=0)
        .order_by('-favorites_count')[:limit]
        .values('id', 'name', 'favorites_count')
    )
    return {'top_selling': top_selling, 'top_rated': top_rated, 'most_favorited': most_favorited}


def users_report() -> dict:
    """Активность пользователей: роли, блокировки, новички, топ-покупатели."""
    users = User.objects.all()
    new_threshold = timezone.now() - timedelta(days=NEW_USERS_PERIOD_DAYS)
    top_buyers = list(
        User.objects.annotate(
            orders_count=Count('orders'),
            spent=Coalesce(
                Sum('orders__total', filter=Q(orders__status=Order.Status.DELIVERED)),
                0,
                output_field=DecimalField(),
            ),
        )
        .filter(orders_count__gt=0)
        .order_by('-orders_count')[:TOP_LIMIT]
        .values('id', 'email', 'orders_count', 'spent')
    )
    return {
        'total_users': users.count(),
        'clients': users.filter(role=User.Role.CLIENT).count(),
        'admins': users.filter(role=User.Role.ADMIN).count(),
        'active': users.filter(is_active=True).count(),
        'blocked': users.filter(is_active=False).count(),
        'new_last_30_days': users.filter(date_joined__gte=new_threshold).count(),
        'top_buyers': top_buyers,
    }


def low_stock_report(threshold: int = LOW_STOCK_THRESHOLD) -> dict:
    """Наборы с низким остатком для пополнения склада."""
    products = Product.objects.filter(is_active=True, stock__lte=threshold).order_by('stock')
    return {
        'threshold': threshold,
        'count': products.count(),
        'products': list(products.values('id', 'name', 'article', 'stock')),
    }
