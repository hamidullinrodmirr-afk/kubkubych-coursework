from datetime import date, timedelta, time
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from doctors.models import Specialty, Doctor, Schedule
from pets.models import Pet
from services.models import Service
from .models import Appointment

User = get_user_model()


class AppointmentTestMixin:
    """Общие данные для тестов записей"""

    def create_test_data(self):
        self.client_api = APIClient()

        self.cardiology = Specialty.objects.create(name='Кардиология')
        self.dermatology = Specialty.objects.create(name='Дерматология')

        self.vet_user = User.objects.create_user(
            email='vet@example.com', password='pass123',
            first_name='Алексей', last_name='Иванов',
            role='veterinarian',
        )
        self.doctor = Doctor.objects.create(
            user=self.vet_user, experience_years=5,
            consultation_price=3000, is_available=True,
        )
        self.doctor.specialties.add(self.cardiology)

        for day in range(5):
            Schedule.objects.create(
                doctor=self.doctor, day_of_week=day,
                start_time='09:00', end_time='17:00', slot_duration=30,
            )

        self.patient = User.objects.create_user(
            email='patient@example.com', password='pass123',
            first_name='Мария', last_name='Петрова',
        )
        self.pet = Pet.objects.create(
            owner=self.patient, name='Мурка',
            species='cat', breed='Персидская', age=48, weight=4.5,
        )
        self.service = Service.objects.create(
            name='ЭКГ', price=2500, duration_minutes=30,
            specialty=self.cardiology,
        )
        self.service_derma = Service.objects.create(
            name='Осмотр кожи', price=1500, duration_minutes=30,
            specialty=self.dermatology,
        )

        today = date.today()
        self.next_monday = today + timedelta(days=(7 - today.weekday()))


class AppointmentCreateTest(AppointmentTestMixin, TestCase):
    """Тест 6: Создание записи на приём"""

    def setUp(self):
        self.create_test_data()
        self.client_api.force_authenticate(user=self.patient)

    def test_create_appointment_success(self):
        data = {
            'doctor': self.doctor.id,
            'pet': self.pet.id,
            'service': self.service.id,
            'date': self.next_monday.isoformat(),
            'time_slot': '10:00',
            'comment': 'Плановый осмотр',
        }
        response = self.client_api.post('/api/appointments/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Appointment.objects.filter(
            client=self.patient, doctor=self.doctor,
        ).exists())

    def test_create_succeeds_when_task_broker_down(self):
        """Сбой брокера задач (Redis недоступен) не должен ломать создание записи."""
        from unittest.mock import patch
        data = {
            'doctor': self.doctor.id,
            'pet': self.pet.id,
            'service': self.service.id,
            'date': self.next_monday.isoformat(),
            'time_slot': '11:00',
            'comment': '',
        }
        with patch(
            'appointments.tasks.send_appointment_confirmation.delay',
            side_effect=OSError('Error connecting to redis'),
        ):
            response = self.client_api.post('/api/appointments/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Appointment.objects.filter(
            client=self.patient, time_slot=time(11, 0),
        ).exists())


class BusySlotValidationTest(AppointmentTestMixin, TestCase):
    """Тест 3: Запись на занятый слот"""

    def setUp(self):
        self.create_test_data()
        self.client_api.force_authenticate(user=self.patient)

        Appointment.objects.create(
            client=self.patient, doctor=self.doctor,
            pet=self.pet, service=self.service,
            date=self.next_monday, time_slot=time(10, 0),
            status='confirmed',
        )

    def test_busy_slot_rejected(self):
        data = {
            'doctor': self.doctor.id,
            'pet': self.pet.id,
            'service': self.service.id,
            'date': self.next_monday.isoformat(),
            'time_slot': '10:00',
        }
        response = self.client_api.post('/api/appointments/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('time_slot', str(response.data))


class DoctorServiceMismatchTest(AppointmentTestMixin, TestCase):
    """Тест 4: Несоответствие врача и услуги"""

    def setUp(self):
        self.create_test_data()
        self.client_api.force_authenticate(user=self.patient)

    def test_wrong_specialty_rejected(self):
        data = {
            'doctor': self.doctor.id,
            'pet': self.pet.id,
            'service': self.service_derma.id,
            'date': self.next_monday.isoformat(),
            'time_slot': '10:00',
        }
        response = self.client_api.post('/api/appointments/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('service', str(response.data))


class AppointmentAccessTest(AppointmentTestMixin, TestCase):
    """Тест 9: Клиент не видит чужие записи"""

    def setUp(self):
        self.create_test_data()

        self.other_patient = User.objects.create_user(
            email='other@example.com', password='pass123',
            first_name='Другой', last_name='Клиент',
        )
        other_pet = Pet.objects.create(
            owner=self.other_patient, name='Бобик',
            species='dog', breed='Овчарка', age=36, weight=25,
        )
        Appointment.objects.create(
            client=self.other_patient, doctor=self.doctor,
            pet=other_pet, service=self.service,
            date=self.next_monday, time_slot=time(11, 0),
        )
        Appointment.objects.create(
            client=self.patient, doctor=self.doctor,
            pet=self.pet, service=self.service,
            date=self.next_monday, time_slot=time(12, 0),
        )

    def test_client_sees_only_own_appointments(self):
        self.client_api.force_authenticate(user=self.patient)
        response = self.client_api.get('/api/appointments/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(
            response.data['results'][0]['client_name'],
            'Петрова Мария',
        )


class AppointmentCancelTest(AppointmentTestMixin, TestCase):
    """Тест 11: Отмена записи"""

    def setUp(self):
        self.create_test_data()
        self.client_api.force_authenticate(user=self.patient)
        self.appointment = Appointment.objects.create(
            client=self.patient, doctor=self.doctor,
            pet=self.pet, service=self.service,
            date=self.next_monday, time_slot=time(14, 0),
            status='confirmed',
        )

    def test_cancel_appointment(self):
        response = self.client_api.post(
            f'/api/appointments/{self.appointment.id}/cancel/',
            {'cancel_reason': 'Питомец выздоровел'},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, 'cancelled')
        self.assertEqual(self.appointment.cancel_reason, 'Питомец выздоровел')

    def test_cannot_cancel_completed(self):
        self.appointment.status = 'completed'
        self.appointment.save()
        response = self.client_api.post(
            f'/api/appointments/{self.appointment.id}/cancel/',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class AppointmentStatusPermissionTest(AppointmentTestMixin, TestCase):
    """Тесты 13-16: Подтверждение и завершение приёма доступны только врачу/админу"""

    def setUp(self):
        self.create_test_data()
        self.appointment = Appointment.objects.create(
            client=self.patient, doctor=self.doctor,
            pet=self.pet, service=self.service,
            date=self.next_monday, time_slot=time(10, 0),
            status='pending',
        )

    def test_client_cannot_confirm(self):
        self.client_api.force_authenticate(user=self.patient)
        response = self.client_api.post(
            f'/api/appointments/{self.appointment.id}/confirm/',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, 'pending')

    def test_vet_confirms_own_appointment(self):
        self.client_api.force_authenticate(user=self.vet_user)
        response = self.client_api.post(
            f'/api/appointments/{self.appointment.id}/confirm/',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, 'confirmed')

    def test_client_cannot_complete(self):
        self.appointment.status = 'confirmed'
        self.appointment.save()
        self.client_api.force_authenticate(user=self.patient)
        response = self.client_api.post(
            f'/api/appointments/{self.appointment.id}/complete/',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_vet_completes_confirmed_appointment(self):
        self.appointment.status = 'confirmed'
        self.appointment.save()
        self.client_api.force_authenticate(user=self.vet_user)
        response = self.client_api.post(
            f'/api/appointments/{self.appointment.id}/complete/',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.appointment.refresh_from_db()
        self.assertEqual(self.appointment.status, 'completed')


class SlotGridValidationTest(AppointmentTestMixin, TestCase):
    """Тест 17: Время записи должно совпадать с сеткой слотов врача"""

    def setUp(self):
        self.create_test_data()
        self.client_api.force_authenticate(user=self.patient)

    def test_misaligned_slot_rejected(self):
        data = {
            'doctor': self.doctor.id,
            'pet': self.pet.id,
            'service': self.service.id,
            'date': self.next_monday.isoformat(),
            'time_slot': '10:07',
        }
        response = self.client_api.post('/api/appointments/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('time_slot', str(response.data))

    def test_aligned_slot_accepted(self):
        data = {
            'doctor': self.doctor.id,
            'pet': self.pet.id,
            'service': self.service.id,
            'date': self.next_monday.isoformat(),
            'time_slot': '10:30',
        }
        response = self.client_api.post('/api/appointments/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)


class DoubleBookingConstraintTest(AppointmentTestMixin, TestCase):
    """Тест 18: Уникальное ограничение БД на активный слот врача"""

    def setUp(self):
        self.create_test_data()

    def test_duplicate_active_slot_raises(self):
        from django.db import IntegrityError, transaction
        Appointment.objects.create(
            client=self.patient, doctor=self.doctor,
            pet=self.pet, service=self.service,
            date=self.next_monday, time_slot=time(10, 0),
            status='confirmed',
        )
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Appointment.objects.create(
                    client=self.patient, doctor=self.doctor,
                    pet=self.pet, service=self.service,
                    date=self.next_monday, time_slot=time(10, 0),
                    status='pending',
                )

    def test_cancelled_slot_can_be_rebooked(self):
        Appointment.objects.create(
            client=self.patient, doctor=self.doctor,
            pet=self.pet, service=self.service,
            date=self.next_monday, time_slot=time(10, 0),
            status='cancelled',
        )
        appointment = Appointment.objects.create(
            client=self.patient, doctor=self.doctor,
            pet=self.pet, service=self.service,
            date=self.next_monday, time_slot=time(10, 0),
            status='pending',
        )
        self.assertIsNotNone(appointment.id)


class MedicalRecordPermissionTest(AppointmentTestMixin, TestCase):
    """Тесты 19-22: Медкарту заполняет только врач завершённого приёма"""

    def setUp(self):
        self.create_test_data()
        self.completed_appt = Appointment.objects.create(
            client=self.patient, doctor=self.doctor,
            pet=self.pet, service=self.service,
            date=self.next_monday - timedelta(days=7), time_slot=time(10, 0),
            status='completed',
        )
        self.record_data = {
            'appointment': None,
            'diagnosis': 'Лёгкая аритмия',
            'treatment': 'Курс препаратов на 14 дней',
            'recommendations': 'Контрольный осмотр через месяц',
        }

    def test_client_cannot_create_record(self):
        self.client_api.force_authenticate(user=self.patient)
        self.record_data['appointment'] = self.completed_appt.id
        response = self.client_api.post('/api/medical-records/', self.record_data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_vet_creates_record_for_own_completed(self):
        self.client_api.force_authenticate(user=self.vet_user)
        self.record_data['appointment'] = self.completed_appt.id
        response = self.client_api.post('/api/medical-records/', self.record_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['pet'], self.pet.id)
        self.assertEqual(response.data['doctor'], self.doctor.id)

    def test_vet_cannot_create_record_for_pending(self):
        pending = Appointment.objects.create(
            client=self.patient, doctor=self.doctor,
            pet=self.pet, service=self.service,
            date=self.next_monday, time_slot=time(11, 0),
            status='pending',
        )
        self.client_api.force_authenticate(user=self.vet_user)
        self.record_data['appointment'] = pending.id
        response = self.client_api.post('/api/medical-records/', self.record_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_vet_cannot_create_record_for_foreign_appointment(self):
        other_vet = User.objects.create_user(
            email='vet2@example.com', password='pass123',
            first_name='Елена', last_name='Сидорова',
            role='veterinarian',
        )
        Doctor.objects.create(
            user=other_vet, experience_years=3,
            consultation_price=2000, is_available=True,
        )
        self.client_api.force_authenticate(user=other_vet)
        self.record_data['appointment'] = self.completed_appt.id
        response = self.client_api.post('/api/medical-records/', self.record_data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
