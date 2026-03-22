from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Appointment, MedicalRecord
from .serializers import (
    AppointmentCreateSerializer, AppointmentListSerializer,
    AppointmentDetailSerializer, AppointmentCancelSerializer,
    MedicalRecordSerializer,
)


class AppointmentViewSet(viewsets.ModelViewSet):
    filterset_fields = ['status', 'date']
    ordering_fields = ['date', 'time_slot', 'created_at']
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Appointment.objects.select_related(
            'client', 'doctor__user', 'pet', 'service',
        )
        if user.role == 'admin':
            return qs
        elif user.role == 'veterinarian':
            return qs.filter(doctor__user=user)
        return qs.filter(client=user)

    def get_serializer_class(self):
        if self.action == 'create':
            return AppointmentCreateSerializer
        if self.action == 'retrieve':
            return AppointmentDetailSerializer
        return AppointmentListSerializer

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        appointment = self.get_object()
        if appointment.status in (Appointment.Status.COMPLETED, Appointment.Status.CANCELLED):
            return Response(
                {'error': 'Невозможно отменить эту запись'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = AppointmentCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        appointment.status = Appointment.Status.CANCELLED
        appointment.cancel_reason = serializer.validated_data.get('cancel_reason', '')
        appointment.save()
        return Response(AppointmentDetailSerializer(appointment).data)

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        appointment = self.get_object()
        if appointment.status != Appointment.Status.PENDING:
            return Response(
                {'error': 'Можно подтвердить только запись со статусом "Ожидание"'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        appointment.status = Appointment.Status.CONFIRMED
        appointment.save()
        return Response(AppointmentDetailSerializer(appointment).data)

    @action(detail=True, methods=['post'])
    def complete(self, request, pk=None):
        appointment = self.get_object()
        if appointment.status not in (Appointment.Status.CONFIRMED, Appointment.Status.IN_PROGRESS):
            return Response(
                {'error': 'Невозможно завершить эту запись'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        appointment.status = Appointment.Status.COMPLETED
        appointment.save()
        return Response(AppointmentDetailSerializer(appointment).data)


class MedicalRecordViewSet(viewsets.ModelViewSet):
    serializer_class = MedicalRecordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = MedicalRecord.objects.select_related(
            'appointment__client', 'pet', 'doctor__user',
        )
        if user.role == 'admin':
            return qs
        elif user.role == 'veterinarian':
            return qs.filter(doctor__user=user)
        return qs.filter(pet__owner=user)
