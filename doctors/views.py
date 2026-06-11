from datetime import datetime, timedelta
from typing import Any

from django.db.models import Avg, Count, Q, QuerySet
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.response import Response

from .filters import DoctorFilter
from .models import Specialty, Doctor
from .serializers import (
    SpecialtySerializer, DoctorListSerializer, DoctorDetailSerializer,
    DoctorCreateSerializer, DoctorUpdateSerializer, ScheduleSerializer,
)
from users.permissions import IsAdmin, IsAdminOrOwnDoctorProfile
from appointments.models import Appointment


class SpecialtyViewSet(viewsets.ModelViewSet):
    """CRUD специализаций: чтение доступно всем, изменение — администратору."""

    queryset = Specialty.objects.all()
    serializer_class = SpecialtySerializer

    def get_permissions(self) -> list[BasePermission]:
        """Права доступа в зависимости от действия."""
        if self.action in ('list', 'retrieve'):
            return [permissions.AllowAny()]
        return [IsAdmin()]


class DoctorViewSet(viewsets.ModelViewSet):
    """Каталог врачей с фильтрацией, поиском, рейтингом и расписанием."""

    filterset_class = DoctorFilter
    search_fields = ['user__first_name', 'user__last_name', 'specialties__name']
    ordering_fields = ['consultation_price', 'experience_years']

    def get_queryset(self) -> QuerySet[Doctor]:
        """Queryset врачей с аннотациями рейтинга и количества отзывов.

        Returns:
            Queryset с ``select_related``/``prefetch_related`` и аннотациями
            ``_avg_rating`` и ``_reviews_count`` по одобренным отзывам.
        """
        return Doctor.objects.select_related('user').prefetch_related('specialties').annotate(
            _avg_rating=Avg('reviews__rating', filter=Q(reviews__is_approved=True)),
            _reviews_count=Count('reviews', filter=Q(reviews__is_approved=True)),
        ).order_by('user__last_name').distinct()

    def get_serializer_class(self) -> type:
        """Сериализатор в зависимости от действия."""
        if self.action == 'retrieve':
            return DoctorDetailSerializer
        if self.action == 'create':
            return DoctorCreateSerializer
        if self.action in ('update', 'partial_update'):
            return DoctorUpdateSerializer
        return DoctorListSerializer

    def get_serializer_context(self) -> dict[str, Any]:
        """Передаёт в сериализатор список врачей, у которых клиент уже был.

        Отдельным запросом собираются идентификаторы врачей с завершёнными
        приёмами текущего пользователя; сериализатор использует их для
        вычисления флага ``is_my_doctor``.

        Returns:
            Контекст сериализатора с ключом ``visited_doctor_ids``.
        """
        context = super().get_serializer_context()
        user = self.request.user
        visited: set[int] = set()
        if user.is_authenticated:
            visited = set(
                Appointment.objects.filter(
                    client=user,
                    status=Appointment.Status.COMPLETED,
                ).values_list('doctor_id', flat=True)
            )
        context['visited_doctor_ids'] = visited
        return context

    def get_permissions(self) -> list[BasePermission]:
        """Права доступа: чтение — всем, правка профиля — админу или самому врачу."""
        if self.action in ('list', 'retrieve', 'schedule', 'available_slots', 'reviews'):
            return [permissions.AllowAny()]
        if self.action in ('update', 'partial_update'):
            return [IsAdminOrOwnDoctorProfile()]
        return [IsAdmin()]

    @action(detail=True, methods=['get'])
    def schedule(self, request: Request, pk: int | None = None) -> Response:
        """Расписание врача по дням недели.

        Args:
            request: HTTP-запрос.
            pk: Идентификатор врача.

        Returns:
            Список интервалов расписания.
        """
        doctor = self.get_object()
        schedules = doctor.schedules.all()
        return Response(ScheduleSerializer(schedules, many=True).data)

    @action(detail=True, methods=['get'], url_path='available-slots')
    def available_slots(self, request: Request, pk: int | None = None) -> Response:
        """Свободные слоты врача на указанную дату.

        Свободное время вычисляется пересечением расписания врача
        и уже существующих неотменённых записей; прошедшие на текущий
        момент слоты исключаются.

        Args:
            request: HTTP-запрос с обязательным параметром ``date``.
            pk: Идентификатор врача.

        Returns:
            Ответ вида ``{"date": ..., "slots": ["10:00", ...]}``
            либо ошибка 400 при отсутствии или неверном формате даты.
        """
        doctor = self.get_object()
        date_str = request.query_params.get('date')
        if not date_str:
            return Response(
                {'error': 'Укажите параметр date (YYYY-MM-DD)'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return Response(
                {'error': 'Неверный формат даты'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        day_of_week = target_date.weekday()
        schedules = doctor.schedules.filter(day_of_week=day_of_week)

        busy_slots = set(
            Appointment.objects.filter(
                doctor=doctor,
                date=target_date,
            ).exclude(
                status=Appointment.Status.CANCELLED,
            ).values_list('time_slot', flat=True)
        )

        now = timezone.localtime()
        available: list[str] = []
        for sched in schedules:
            current = datetime.combine(target_date, sched.start_time)
            end = datetime.combine(target_date, sched.end_time)
            delta = timedelta(minutes=sched.slot_duration)
            while current + delta <= end:
                t = current.time()
                is_past = target_date == now.date() and t <= now.time()
                if t not in busy_slots and not is_past:
                    available.append(t.strftime('%H:%M'))
                current += delta

        return Response({'date': date_str, 'slots': available})

    @action(detail=True, methods=['get'])
    def reviews(self, request: Request, pk: int | None = None) -> Response:
        """Одобренные отзывы о враче с пагинацией.

        Args:
            request: HTTP-запрос.
            pk: Идентификатор врача.

        Returns:
            Страница отзывов либо полный список без пагинации.
        """
        from reviews.serializers import ReviewListSerializer
        doctor = self.get_object()
        qs = doctor.reviews.filter(is_approved=True).select_related('author')
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(ReviewListSerializer(page, many=True).data)
        return Response(ReviewListSerializer(qs, many=True).data)
