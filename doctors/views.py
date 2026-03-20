from datetime import datetime, timedelta
from django.db.models import Avg, Count, Q
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Specialty, Doctor, Schedule
from .serializers import (
    SpecialtySerializer, DoctorListSerializer,
    DoctorDetailSerializer, DoctorCreateSerializer, ScheduleSerializer,
)
from users.permissions import IsAdmin
from appointments.models import Appointment


class SpecialtyViewSet(viewsets.ModelViewSet):
    queryset = Specialty.objects.all()
    serializer_class = SpecialtySerializer

    def get_permissions(self):
        if self.action in ('list', 'retrieve'):
            return [permissions.AllowAny()]
        return [IsAdmin()]


class DoctorViewSet(viewsets.ModelViewSet):
    filterset_fields = ['is_available']
    search_fields = ['user__first_name', 'user__last_name']
    ordering_fields = ['consultation_price', 'experience_years']

    def get_queryset(self):
        qs = Doctor.objects.select_related('user').prefetch_related('specialties')
        qs = qs.annotate(
            _avg_rating=Avg('reviews__rating', filter=Q(reviews__is_approved=True)),
            _reviews_count=Count('reviews', filter=Q(reviews__is_approved=True)),
        )
        specialty = self.request.query_params.get('specialty')
        if specialty:
            qs = qs.filter(specialties__name__icontains=specialty)
        min_rating = self.request.query_params.get('min_rating')
        if min_rating:
            qs = qs.filter(_avg_rating__gte=float(min_rating))
        return qs.distinct()

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return DoctorDetailSerializer
        if self.action == 'create':
            return DoctorCreateSerializer
        return DoctorListSerializer

    def get_permissions(self):
        if self.action in ('list', 'retrieve', 'schedule', 'available_slots', 'reviews'):
            return [permissions.AllowAny()]
        return [IsAdmin()]

    @action(detail=True, methods=['get'])
    def schedule(self, request, pk=None):
        doctor = self.get_object()
        schedules = doctor.schedules.all()
        return Response(ScheduleSerializer(schedules, many=True).data)

    @action(detail=True, methods=['get'], url_path='available-slots')
    def available_slots(self, request, pk=None):
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

        available = []
        for sched in schedules:
            current = datetime.combine(target_date, sched.start_time)
            end = datetime.combine(target_date, sched.end_time)
            delta = timedelta(minutes=sched.slot_duration)
            while current + delta <= end:
                t = current.time()
                if t not in busy_slots:
                    available.append(t.strftime('%H:%M'))
                current += delta

        return Response({'date': date_str, 'slots': available})

    @action(detail=True, methods=['get'])
    def reviews(self, request, pk=None):
        from reviews.serializers import ReviewListSerializer
        doctor = self.get_object()
        qs = doctor.reviews.filter(is_approved=True).select_related('author')
        page = self.paginate_queryset(qs)
        if page is not None:
            return self.get_paginated_response(ReviewListSerializer(page, many=True).data)
        return Response(ReviewListSerializer(qs, many=True).data)
