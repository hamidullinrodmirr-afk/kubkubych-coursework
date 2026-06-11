from django.db.models import QuerySet
from rest_framework import mixins, viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.permissions import BasePermission
from rest_framework.request import Request
from rest_framework.response import Response

from .filters import AppointmentFilter
from .models import Appointment, MedicalRecord
from .serializers import (
    AppointmentCreateSerializer, AppointmentListSerializer,
    AppointmentDetailSerializer, AppointmentCancelSerializer,
    MedicalRecordSerializer,
)
from users.permissions import IsAdmin, IsVeterinarian


class AppointmentViewSet(mixins.CreateModelMixin,
                         mixins.RetrieveModelMixin,
                         mixins.ListModelMixin,
                         viewsets.GenericViewSet):
    """Записи на приём: клиент видит свои, врач — назначенные ему, админ — все.

    Прямое изменение и удаление записей не предусмотрено: статус меняется
    только действиями cancel/confirm/complete. Подтверждение и завершение
    приёма доступны врачу записи или администратору; отмена — клиенту
    (до начала приёма), врачу и администратору.
    """

    filterset_class = AppointmentFilter
    ordering_fields = ['date', 'time_slot', 'created_at']
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet[Appointment]:
        """Queryset записей, ограниченный ролью текущего пользователя."""
        user = self.request.user
        qs = Appointment.objects.select_related(
            'client', 'doctor__user', 'pet', 'service',
        )
        if user.role == 'admin':
            return qs
        elif user.role == 'veterinarian':
            return qs.filter(doctor__user=user)
        return qs.filter(client=user)

    def get_serializer_class(self) -> type:
        """Сериализатор в зависимости от действия."""
        if self.action == 'create':
            return AppointmentCreateSerializer
        if self.action == 'retrieve':
            return AppointmentDetailSerializer
        return AppointmentListSerializer

    def perform_create(self, serializer: AppointmentCreateSerializer) -> None:
        """Сохраняет запись и ставит в очередь письмо-подтверждение.

        Args:
            serializer: Валидированный сериализатор создания записи.
        """
        appointment = serializer.save()
        from appointments.tasks import enqueue, send_appointment_confirmation
        enqueue(send_appointment_confirmation, appointment.id)

    def _is_appointment_manager(self, appointment: Appointment) -> bool:
        """Может ли текущий пользователь управлять статусом записи.

        Args:
            appointment: Проверяемая запись.

        Returns:
            True для администратора и врача, на которого назначена запись.
        """
        user = self.request.user
        if user.role == 'admin':
            return True
        return user.role == 'veterinarian' and appointment.doctor.user_id == user.id

    @action(detail=True, methods=['post'])
    def cancel(self, request: Request, pk: int | None = None) -> Response:
        """Отмена записи с опциональной причиной.

        Клиент может отменить только свою запись в статусах «Ожидание»
        и «Подтверждён»; врач и администратор — любую незавершённую.

        Args:
            request: HTTP-запрос с полем ``cancel_reason``.
            pk: Идентификатор записи.

        Returns:
            Детальная карточка записи либо ошибка 400/403.
        """
        appointment = self.get_object()
        if appointment.status in (Appointment.Status.COMPLETED, Appointment.Status.CANCELLED):
            return Response(
                {'error': 'Невозможно отменить эту запись'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        is_client = request.user.role == 'client'
        client_allowed = (Appointment.Status.PENDING, Appointment.Status.CONFIRMED)
        if is_client and appointment.status not in client_allowed:
            return Response(
                {'error': 'Приём уже начался — отмена недоступна'},
                status=status.HTTP_403_FORBIDDEN,
            )
        serializer = AppointmentCancelSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        appointment.status = Appointment.Status.CANCELLED
        appointment.cancel_reason = serializer.validated_data.get('cancel_reason', '')
        appointment.save()
        return Response(AppointmentDetailSerializer(appointment, context=self.get_serializer_context()).data)

    @action(detail=True, methods=['post'])
    def confirm(self, request: Request, pk: int | None = None) -> Response:
        """Подтверждение записи врачом или администратором.

        Args:
            request: HTTP-запрос.
            pk: Идентификатор записи.

        Returns:
            Детальная карточка записи либо ошибка 400/403.
        """
        appointment = self.get_object()
        if not self._is_appointment_manager(appointment):
            return Response(
                {'error': 'Подтверждать запись может только врач или администратор'},
                status=status.HTTP_403_FORBIDDEN,
            )
        if appointment.status != Appointment.Status.PENDING:
            return Response(
                {'error': 'Можно подтвердить только запись со статусом "Ожидание"'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        appointment.status = Appointment.Status.CONFIRMED
        appointment.save()
        from appointments.tasks import enqueue, send_appointment_confirmation
        enqueue(send_appointment_confirmation, appointment.id)
        return Response(AppointmentDetailSerializer(appointment, context=self.get_serializer_context()).data)

    @action(detail=True, methods=['post'])
    def complete(self, request: Request, pk: int | None = None) -> Response:
        """Завершение приёма врачом или администратором.

        Args:
            request: HTTP-запрос.
            pk: Идентификатор записи.

        Returns:
            Детальная карточка записи либо ошибка 400/403.
        """
        appointment = self.get_object()
        if not self._is_appointment_manager(appointment):
            return Response(
                {'error': 'Завершать приём может только врач или администратор'},
                status=status.HTTP_403_FORBIDDEN,
            )
        if appointment.status not in (Appointment.Status.CONFIRMED, Appointment.Status.IN_PROGRESS):
            return Response(
                {'error': 'Невозможно завершить эту запись'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        appointment.status = Appointment.Status.COMPLETED
        appointment.save()
        return Response(AppointmentDetailSerializer(appointment, context=self.get_serializer_context()).data)


class MedicalRecordViewSet(viewsets.ModelViewSet):
    """Медицинские карты: чтение — по роли, изменение — врач и администратор."""

    serializer_class = MedicalRecordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self) -> QuerySet[MedicalRecord]:
        """Queryset карт, ограниченный ролью текущего пользователя."""
        user = self.request.user
        qs = MedicalRecord.objects.select_related(
            'appointment__client', 'pet', 'doctor__user',
        )
        if user.role == 'admin':
            return qs
        elif user.role == 'veterinarian':
            return qs.filter(doctor__user=user)
        return qs.filter(pet__owner=user)

    def get_permissions(self) -> list[BasePermission]:
        """Изменение карт доступно только ветеринару или администратору."""
        if self.action in ('create', 'update', 'partial_update', 'destroy'):
            return [(IsVeterinarian | IsAdmin)()]
        return [permissions.IsAuthenticated()]
