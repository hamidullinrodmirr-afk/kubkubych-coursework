from datetime import date, timedelta, time
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from doctors.models import Specialty, Doctor, Schedule
from pets.models import Pet
from services.models import Service
from appointments.models import Appointment
from .models import Review

User = get_user_model()


class ReviewWithoutCompletedAppointmentTest(TestCase):
    """Тест 5: Отзыв без завершённого приёма"""

    def setUp(self):
        self.client_api = APIClient()

        self.cardiology = Specialty.objects.create(name='Кардиология')
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

        today = date.today()
        next_monday = today + timedelta(days=(7 - today.weekday()))

        # Приём в статусе "ожидание" (не завершён)
        self.pending_appt = Appointment.objects.create(
            client=self.patient, doctor=self.doctor,
            pet=self.pet, service=self.service,
            date=next_monday, time_slot=time(10, 0),
            status='pending',
        )

        self.client_api.force_authenticate(user=self.patient)

    def test_review_without_completed_appointment_rejected(self):
        data = {
            'doctor': self.doctor.id,
            'appointment': self.pending_appt.id,
            'rating': 5,
            'text': 'Отличный врач, рекомендую всем знакомым!',
        }
        response = self.client_api.post('/api/reviews/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('appointment', str(response.data))

    def test_review_with_completed_appointment_success(self):
        self.pending_appt.status = 'completed'
        self.pending_appt.save()

        data = {
            'doctor': self.doctor.id,
            'appointment': self.pending_appt.id,
            'rating': 5,
            'text': 'Отличный врач, рекомендую всем знакомым!',
        }
        response = self.client_api.post('/api/reviews/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Review.objects.filter(
            author=self.patient, doctor=self.doctor,
        ).exists())

    def test_duplicate_review_rejected(self):
        self.pending_appt.status = 'completed'
        self.pending_appt.save()

        Review.objects.create(
            author=self.patient, doctor=self.doctor,
            appointment=self.pending_appt,
            rating=5, text='Первый отзыв, всё понравилось!',
        )

        data = {
            'doctor': self.doctor.id,
            'appointment': self.pending_appt.id,
            'rating': 4,
            'text': 'Попытка второго отзыва на тот же приём',
        }
        response = self.client_api.post('/api/reviews/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
