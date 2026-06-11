from datetime import date, time, timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from appointments.models import Appointment
from doctors.models import Specialty, Doctor
from pets.models import Pet
from .models import Service

User = get_user_model()


class ServiceTestMixin:
    """Общие данные для тестов услуг"""

    def create_test_data(self):
        self.client_api = APIClient()

        self.cardiology = Specialty.objects.create(name='Кардиология')
        self.active_service = Service.objects.create(
            name='ЭКГ', price=2500, duration_minutes=30,
            specialty=self.cardiology, is_active=True,
        )
        self.inactive_service = Service.objects.create(
            name='Старая услуга', price=1000, duration_minutes=30,
            specialty=self.cardiology, is_active=False,
        )

        self.admin = User.objects.create_user(
            email='admin@example.com', password='pass123',
            first_name='Админ', last_name='Главный',
            role='admin',
        )


class ServiceVisibilityTest(ServiceTestMixin, TestCase):
    """Тесты 34-35: Неактивные услуги видны только администратору"""

    def setUp(self):
        self.create_test_data()

    def test_anonymous_sees_only_active(self):
        response = self.client_api.get('/api/services/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [s['name'] for s in response.data['results']]
        self.assertEqual(names, ['ЭКГ'])

    def test_admin_sees_inactive(self):
        self.client_api.force_authenticate(user=self.admin)
        response = self.client_api.get('/api/services/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [s['name'] for s in response.data['results']]
        self.assertIn('Старая услуга', names)


class ServiceAnnotationTest(ServiceTestMixin, TestCase):
    """Тест 36: Аннотации популярности услуги в API"""

    def setUp(self):
        self.create_test_data()

        vet_user = User.objects.create_user(
            email='vet@example.com', password='pass123',
            first_name='Алексей', last_name='Иванов',
            role='veterinarian',
        )
        doctor = Doctor.objects.create(
            user=vet_user, experience_years=5,
            consultation_price=3000, is_available=True,
        )
        doctor.specialties.add(self.cardiology)

        patient = User.objects.create_user(
            email='patient@example.com', password='pass123',
            first_name='Мария', last_name='Петрова',
        )
        pet = Pet.objects.create(
            owner=patient, name='Мурка',
            species='cat', breed='Персидская', age=48, weight=4.5,
        )

        base_date = date.today() - timedelta(days=30)
        for offset, appt_status in enumerate(['completed', 'completed', 'pending']):
            Appointment.objects.create(
                client=patient, doctor=doctor,
                pet=pet, service=self.active_service,
                date=base_date + timedelta(days=offset),
                time_slot=time(10, 0),
                status=appt_status,
            )

    def test_bookings_annotations_in_response(self):
        response = self.client_api.get('/api/services/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        service_data = next(
            s for s in response.data['results'] if s['name'] == 'ЭКГ'
        )
        self.assertEqual(service_data['total_bookings'], 3)
        self.assertEqual(service_data['completed_bookings'], 2)
