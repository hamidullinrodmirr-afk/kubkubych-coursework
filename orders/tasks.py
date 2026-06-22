"""Фоновые задачи Celery: письма по заказам и периодические отчёты."""

from datetime import timedelta

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Count, Sum
from django.utils import timezone

from .constants import STALE_ORDER_HOURS
from .models import Order, OrderItem


def _admin_recipients() -> list[str]:
    """Список адресов администраторов с резервом из настроек."""
    from users.models import User

    emails = list(
        User.objects.filter(role=User.Role.ADMIN, is_active=True).values_list('email', flat=True)
    )
    admin_email = getattr(settings, 'ADMIN_EMAIL', '')
    if admin_email and admin_email not in emails:
        emails.append(admin_email)
    return emails


@shared_task
def send_order_confirmation_email(order_id: int) -> str:
    """Письмо покупателю о принятом заказе."""
    order = Order.objects.select_related('user').get(pk=order_id)
    send_mail(
        subject=f'Заказ {order.order_number} принят',
        message=(
            f'Здравствуйте, {order.recipient_name}!\n\n'
            f'Ваш заказ {order.order_number} на сумму {order.total} ₽ принят в обработку.\n'
            f'Адрес доставки: {order.delivery_address}.\n'
            f'Статус: {order.get_status_display()}.\n\n'
            'Спасибо, что выбрали КубКубыч!'
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[order.user.email],
        fail_silently=True,
    )
    return order.order_number


@shared_task
def send_order_status_email(order_id: int, old_status: str, new_status: str) -> str:
    """Письмо покупателю о смене статуса заказа."""
    order = Order.objects.select_related('user').get(pk=order_id)
    names = dict(Order.Status.choices)
    send_mail(
        subject=f'Заказ {order.order_number}: статус обновлён',
        message=(
            f'Здравствуйте, {order.recipient_name}!\n\n'
            f'Статус заказа {order.order_number} изменился: '
            f'«{names.get(old_status, old_status)}» → «{names.get(new_status, new_status)}».'
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[order.user.email],
        fail_silently=True,
    )
    return order.order_number


@shared_task
def send_daily_sales_report() -> str:
    """Ежедневный отчёт администраторам: заказы, выручка, новые покупатели, топ-5."""
    from users.models import User

    today = timezone.now().date()
    todays_orders = Order.objects.filter(created_at__date=today)
    delivered = todays_orders.filter(status=Order.Status.DELIVERED)
    revenue = delivered.aggregate(total=Sum('total'))['total'] or 0
    new_users = User.objects.filter(date_joined__date=today).count()
    top_products = (
        OrderItem.objects.filter(order__status=Order.Status.DELIVERED, order__created_at__date=today)
        .values('product_name')
        .annotate(sold=Sum('quantity'))
        .order_by('-sold')[:5]
    )
    top_lines = '\n'.join(f'  • {row["product_name"]}: {row["sold"]} шт.' for row in top_products) or '  —'
    send_mail(
        subject=f'КубКубыч: отчёт за {today:%d.%m.%Y}',
        message=(
            f'Заказов за день: {todays_orders.count()}\n'
            f'Доставлено и оплачено: {delivered.count()} на сумму {revenue} ₽\n'
            f'Новых покупателей: {new_users}\n\n'
            f'Топ-5 наборов:\n{top_lines}'
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=_admin_recipients(),
        fail_silently=True,
    )
    return f'sales report {today}'


@shared_task
def auto_cancel_stale_orders() -> int:
    """Отменяет новые заказы старше суток и возвращает остатки на склад."""
    from .services import change_order_status

    threshold = timezone.now() - timedelta(hours=STALE_ORDER_HOURS)
    stale = Order.objects.filter(status=Order.Status.NEW, created_at__lt=threshold)
    cancelled = 0
    for order in stale:
        change_order_status(order, Order.Status.CANCELLED)
        cancelled += 1
    return cancelled


@shared_task
def send_low_stock_report() -> int:
    """Сообщает администраторам о наборах с низким остатком."""
    from products.constants import LOW_STOCK_THRESHOLD
    from products.models import Product

    low_stock = (
        Product.objects.filter(is_active=True, stock__lte=LOW_STOCK_THRESHOLD)
        .order_by('stock')
        .values('name', 'article', 'stock')
    )
    if not low_stock:
        return 0
    lines = '\n'.join(f'  • {row["name"]} ({row["article"]}): {row["stock"]} шт.' for row in low_stock)
    send_mail(
        subject='КубКубыч: низкий остаток наборов',
        message=f'Заканчиваются наборы (остаток ≤ {LOW_STOCK_THRESHOLD}):\n\n{lines}',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=_admin_recipients(),
        fail_silently=True,
    )
    return len(low_stock)
