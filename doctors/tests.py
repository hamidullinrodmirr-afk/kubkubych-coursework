from datetime import date, timedelta
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from .models import Specialty, Doctor, Schedule
from appointments.models import Appointment
from pets.models import Pet
from services.models import Service
from reviews.models import Review

User = get_user_model()


class DoctorTestMixin:
    """Общие данные для тестов врачей"""

    def create_test_data(self):
        self.client_api = APIClient()

        self.cardiology = Specialty.objects.create(name='Кардиология')
        self.dermatology = Specialty.objects.create(name='Дерматология')
        self.neurology = Specialty.objects.create(name='Неврология')

        self.vet_user = User.objects.create_user(
            email='vet@example.com', password='pass123',
            first_name='Алексей', last_name='Иванов',
            role='veterinarian',
        )
        self.doctor = Doctor.objects.create(
            user=self.vet_user,
            experience_years=5,
            consultation_price=3000,
            is_available=True,
        )
        self.doctor.specialties.add(self.cardiology)

        for day in range(5):
            Schedule.objects.create(
                doctor=self.doctor,
                day_of_week=day,
                start_time='09:00',
                end_time='17:00',
                slot_duration=30,
            )

        self.patient_user = User.objects.create_user(
            email='patient@example.com', password='pass123',
            first_name='Мария', last_name='Петрова',
        )

        self.pet = Pet.objects.create(
            owner=self.patient_user, name='Мурка',
            species='cat', breed='Персидская', age=48, weight=4.5,
        )

        self.service_cardio = Service.objects.create(
            name='ЭКГ для животных', price=2500,
            duration_minutes=30, specialty=self.cardiology,
        )

        self.service_derma = Service.objects.create(
            name='Осмотр кожи', price=1500,
            duration_minutes=30, specialty=self.dermatology,
        )


class DoctorFilterTest(DoctorTestMixin, TestCase):
    """Тест 7: Фильтрация врачей по специальности"""

    def setUp(self):
        self.create_test_data()

        vet2 = User.objects.create_user(
            email='vet2@example.com', password='pass123',
            first_name='Елена', last_name='Сидорова',
            role='veterinarian',
        )
        self.doctor2 = Doctor.objects.create(
            user=vet2, experience_years=3,
            consultation_price=2000, is_available=True,
        )
        self.doctor2.specialties.add(self.dermatology)

    def test_filter_by_specialty(self):
        response = self.client_api.get('/api/doctors/', {'specialty': 'Кардиология'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [d['full_name'] for d in response.data['results']]
        self.assertIn('Иванов Алексей', names)
        self.assertNotIn('Сидорова Елена', names)

    def test_filter_by_specialty_full_name(self):
        response = self.client_api.get('/api/doctors/', {'specialty': 'Дерматология'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['full_name'], 'Сидорова Елена')


class DoctorRatingAnnotationTest(DoctorTestMixin, TestCase):
    """Тест 8: Аннотация среднего рейтинга врача"""

    def setUp(self):
        self.create_test_data()
        self.client_api.force_authenticate(user=self.patient_user)

        next_monday = date.today() + timedelta(days=(7 - date.today().weekday()))
        for i, rating in enumerate([5, 4, 3]):
            appt = Appointment.objects.create(
                client=self.patient_user, doctor=self.doctor,
                pet=self.pet, service=self.service_cardio,
                date=next_monday - timedelta(days=30 + i),
                time_slot=f'1{i}:00',
                status='completed',
            )
            Review.objects.create(
                author=self.patient_user, doctor=self.doctor,
                appointment=appt, rating=rating,
                text='Отличный специалист, рекомендую всем!',
                is_approved=True,
            )

    def test_avg_rating_in_list(self):
        self.client_api.force_authenticate(user=None)
        response = self.client_api.get('/api/doctors/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        doctor_data = response.data['results'][0]
        self.assertEqual(doctor_data['avg_rating'], 4.0)
        self.assertEqual(doctor_data['reviews_count'], 3)


class DoctorAvailableSlotsTest(DoctorTestMixin, TestCase):
    """Тест 12: Список доступных слотов врача"""

    def setUp(self):
        self.create_test_data()

    def test_available_slots(self):
        today = date.today()
        next_monday = today + timedelta(days=(7 - today.weekday()))

        response = self.client_api.get(
            f'/api/doctors/{self.doctor.id}/available-slots/',
            {'date': next_monday.isoformat()},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        slots = response.data['slots']
        self.assertIn('09:00', slots)
        self.assertIn('16:30', slots)
        self.assertEqual(len(slots), 16)

    def test_slots_exclude_booked(self):
        today = date.today()
        next_monday = today + timedelta(days=(7 - today.weekday()))

        Appointment.objects.create(
            client=self.patient_user, doctor=self.doctor,
            pet=self.pet, service=self.service_cardio,
            date=next_monday, time_slot='10:00',
            status='confirmed',
        )

        response = self.client_api.get(
            f'/api/doctors/{self.doctor.id}/available-slots/',
            {'date': next_monday.isoformat()},
        )
        slots = response.data['slots']
        self.assertNotIn('10:00', slots)
        self.assertEqual(len(slots), 15)

    def test_no_date_param_returns_error(self):
        response = self.client_api.get(
            f'/api/doctors/{self.doctor.id}/available-slots/',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class DoctorFilterSetTest(DoctorTestMixin, TestCase):
    """Тесты 23-25: Фильтрация врачей через DoctorFilter (django-filter)"""

    def setUp(self):
        self.create_test_data()

        vet2 = User.objects.create_user(
            email='vet2@example.com', password='pass123',
            first_name='Елена', last_name='Сидорова',
            role='veterinarian',
        )
        self.doctor2 = Doctor.objects.create(
            user=vet2, experience_years=3,
            consultation_price=2000, is_available=True,
        )
        self.doctor2.specialties.add(self.dermatology)

    def test_filter_by_min_price(self):
        response = self.client_api.get('/api/doctors/', {'min_price': 2500})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [d['full_name'] for d in response.data['results']]
        self.assertEqual(names, ['Иванов Алексей'])

    def test_filter_by_min_experience(self):
        response = self.client_api.get('/api/doctors/', {'min_experience': 4})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        names = [d['full_name'] for d in response.data['results']]
        self.assertEqual(names, ['Иванов Алексей'])

    def test_invalid_min_rating_returns_400(self):
        response = self.client_api.get('/api/doctors/', {'min_rating': 'abc'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class DoctorVisitedContextTest(DoctorTestMixin, TestCase):
    """Тесты 26-27: Флаг is_my_doctor через контекст сериализатора"""

    def setUp(self):
        self.create_test_data()
        next_monday = date.today() + timedelta(days=(7 - date.today().weekday()))
        Appointment.objects.create(
            client=self.patient_user, doctor=self.doctor,
            pet=self.pet, service=self.service_cardio,
            date=next_monday - timedelta(days=14), time_slot='10:00',
            status='completed',
        )

    def test_visited_doctor_flagged_for_client(self):
        self.client_api.force_authenticate(user=self.patient_user)
        response = self.client_api.get('/api/doctors/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['results'][0]['is_my_doctor'])

    def test_flag_false_for_anonymous(self):
        response = self.client_api.get('/api/doctors/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['results'][0]['is_my_doctor'])


class ScheduleValidationTest(DoctorTestMixin, TestCase):
    """Тесты 28-30: Валидация расписания врача"""

    def setUp(self):
        self.create_test_data()

    def test_start_after_end_rejected(self):
        from django.core.exceptions import ValidationError
        schedule = Schedule(
            doctor=self.doctor, day_of_week=6,
            start_time='15:00', end_time='10:00', slot_duration=30,
        )
        with self.assertRaises(ValidationError):
            schedule.full_clean()

    def test_overlapping_interval_rejected(self):
        from django.core.exceptions import ValidationError
        schedule = Schedule(
            doctor=self.doctor, day_of_week=0,
            start_time='10:00', end_time='12:00', slot_duration=30,
        )
        with self.assertRaises(ValidationError):
            schedule.full_clean()

    def test_slot_duration_out_of_bounds_rejected(self):
        from django.core.exceptions import ValidationError
        schedule = Schedule(
            doctor=self.doctor, day_of_week=6,
            start_time='10:00', end_time='12:00', slot_duration=10,
        )
        with self.assertRaises(ValidationError):
            schedule.full_clean()
