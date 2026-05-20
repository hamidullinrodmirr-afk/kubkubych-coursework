import logging
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

logger = logging.getLogger(__name__)


def enqueue(task, *args, **kwargs):
    """Best-effort постановка задачи в очередь без блокировки HTTP-ответа.

    Запись уже сохранена в БД, письмо — побочный эффект (см. инвариант CLAUDE.md).
    При недоступном брокере publish может висеть несколько секунд на таймауте
    подключения — выносим его в daemon-поток, чтобы ответ вернулся сразу.
    В eager-режиме (тесты) выполняем синхронно: детерминированно и без
    обращения к БД из постороннего потока.
    """
    def _run():
        try:
            task.delay(*args, **kwargs)
        except Exception as exc:  # noqa: BLE001 — сбой брокера/сети глушим намеренно
            logger.warning('Не удалось поставить задачу %s в очередь: %s', task.name, exc)

    if getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False):
        _run()
    else:
        import threading
        threading.Thread(target=_run, daemon=True).start()


@shared_task
def send_appointment_confirmation(appointment_id):
    """Отправка подтверждения записи на приём."""
    from appointments.models import Appointment

    try:
        appt = Appointment.objects.select_related(
            'client', 'doctor__user', 'pet', 'service'
        ).get(id=appointment_id)
    except Appointment.DoesNotExist:
        return

    send_mail(
        subject='PetCare — Запись на приём подтверждена',
        message=(
            f'Здравствуйте, {appt.client.first_name}!\n\n'
            f'Ваша запись подтверждена:\n'
            f'Дата: {appt.date.strftime("%d.%m.%Y")}\n'
            f'Время: {appt.time_slot.strftime("%H:%M")}\n'
            f'Врач: {appt.doctor.user.get_full_name()}\n'
            f'Услуга: {appt.service.name}\n'
            f'Питомец: {appt.pet.name}\n\n'
            f'Ждём вас в клинике PetCare!'
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[appt.client.email],
        fail_silently=True,
    )


@shared_task
def send_appointment_reminder():
    """Напоминание о записи за 24 часа."""
    from appointments.models import Appointment

    tomorrow = timezone.now().date() + timedelta(days=1)
    appointments = Appointment.objects.filter(
        date=tomorrow,
        status__in=['pending', 'confirmed'],
    ).select_related('client', 'doctor__user', 'pet', 'service')

    for appt in appointments:
        send_mail(
            subject='PetCare — Напоминание о визите завтра',
            message=(
                f'Здравствуйте, {appt.client.first_name}!\n\n'
                f'Напоминаем о вашем визите завтра:\n'
                f'Дата: {appt.date.strftime("%d.%m.%Y")}\n'
                f'Время: {appt.time_slot.strftime("%H:%M")}\n'
                f'Врач: {appt.doctor.user.get_full_name()}\n'
                f'Услуга: {appt.service.name}\n'
                f'Питомец: {appt.pet.name}\n\n'
                f'Если вам нужно отменить запись, сделайте это '
                f'в личном кабинете на сайте.'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[appt.client.email],
            fail_silently=True,
        )

    return f'Отправлено {appointments.count()} напоминаний'


@shared_task
def auto_cancel_unconfirmed():
    """Автоотмена неподтверждённых записей старше 48 часов."""
    from appointments.models import Appointment

    threshold = timezone.now() - timedelta(hours=48)
    expired = Appointment.objects.filter(
        status='pending',
        created_at__lt=threshold,
    )
    count = expired.update(status='cancelled')
    return f'Автоотменено {count} записей'


@shared_task
def send_daily_report():
    """Ежедневный отчёт администраторам о записях."""
    from appointments.models import Appointment
    from users.models import User

    today = timezone.now().date()
    stats = {
        'total': Appointment.objects.filter(date=today).count(),
        'pending': Appointment.objects.filter(date=today, status='pending').count(),
        'confirmed': Appointment.objects.filter(date=today, status='confirmed').count(),
        'completed': Appointment.objects.filter(date=today, status='completed').count(),
        'cancelled': Appointment.objects.filter(date=today, status='cancelled').count(),
    }

    admins = User.objects.filter(role='admin').values_list('email', flat=True)
    if not admins:
        return 'Нет администраторов для отправки отчёта'

    send_mail(
        subject=f'PetCare — Дневной отчёт за {today.strftime("%d.%m.%Y")}',
        message=(
            f'Отчёт по записям за {today.strftime("%d.%m.%Y")}:\n\n'
            f'Всего записей: {stats["total"]}\n'
            f'Ожидают подтверждения: {stats["pending"]}\n'
            f'Подтверждены: {stats["confirmed"]}\n'
            f'Завершены: {stats["completed"]}\n'
            f'Отменены: {stats["cancelled"]}\n'
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=list(admins),
        fail_silently=True,
    )
    return f'Отчёт отправлен {len(admins)} администраторам'


@shared_task
def cleanup_old_appointments():
    """Очистка завершённых/отменённых записей старше 1 года."""
    from appointments.models import Appointment

    threshold = timezone.now().date() - timedelta(days=365)
    old = Appointment.objects.filter(
        date__lt=threshold,
        status__in=['completed', 'cancelled'],
    )
    count = old.count()
    old.delete()
    return f'Удалено {count} старых записей'
