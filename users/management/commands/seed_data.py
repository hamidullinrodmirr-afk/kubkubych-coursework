from datetime import time, date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from users.models import User
from pets.models import Pet
from doctors.models import Specialty, Doctor, Schedule
from services.models import Service
from appointments.models import Appointment
from reviews.models import Review


class Command(BaseCommand):
    help = 'Заполнение базы тестовыми данными'

    def handle(self, *args, **options):
        self.stdout.write('Создание тестовых данных...')

        # ─── Специализации ──────────────────────
        specs = {}
        spec_data = [
            ('Терапия', 'Общий осмотр, диагностика и лечение', 'stethoscope'),
            ('Хирургия', 'Оперативное лечение и восстановление', 'scalpel'),
            ('Офтальмология', 'Диагностика и лечение заболеваний глаз', 'eye'),
            ('Дерматология', 'Лечение заболеваний кожи и шерсти', 'hand'),
            ('Стоматология', 'Уход за зубами и полостью рта', 'tooth'),
            ('Кардиология', 'Диагностика и лечение сердечных заболеваний', 'heart'),
        ]
        for name, desc, icon in spec_data:
            s, _ = Specialty.objects.get_or_create(
                name=name, defaults={'description': desc, 'icon': icon}
            )
            specs[name] = s
        self.stdout.write(f'  Специализации: {len(specs)}')

        # ─── Ветеринары ─────────────────────────
        doctors_data = [
            {
                'email': 'ivanov@petcare.ru', 'first_name': 'Алексей',
                'last_name': 'Иванов', 'phone': '+7-999-111-11-11',
                'specialties': ['Терапия', 'Кардиология'],
                'experience': 12, 'education': 'МГАВМиБ им. Скрябина',
                'bio': 'Опытный терапевт и кардиолог. Специализируется на лечении собак и кошек.',
                'consultation_price': '2000.00',
            },
            {
                'email': 'petrova@petcare.ru', 'first_name': 'Елена',
                'last_name': 'Петрова', 'phone': '+7-999-222-22-22',
                'specialties': ['Хирургия'],
                'experience': 8, 'education': 'РУДН, ветеринарный факультет',
                'bio': 'Хирург высшей категории. Проводит операции любой сложности.',
                'consultation_price': '2500.00',
            },
            {
                'email': 'sidorov@petcare.ru', 'first_name': 'Дмитрий',
                'last_name': 'Сидоров', 'phone': '+7-999-333-33-33',
                'specialties': ['Офтальмология', 'Терапия'],
                'experience': 6, 'education': 'СПбГАВМ',
                'bio': 'Специалист по заболеваниям глаз у домашних животных.',
                'consultation_price': '1800.00',
            },
            {
                'email': 'kuznetsova@petcare.ru', 'first_name': 'Анна',
                'last_name': 'Кузнецова', 'phone': '+7-999-444-44-44',
                'specialties': ['Дерматология', 'Терапия'],
                'experience': 10, 'education': 'МГАВМиБ им. Скрябина',
                'bio': 'Дерматолог с большим опытом лечения аллергий и кожных заболеваний.',
                'consultation_price': '2200.00',
            },
            {
                'email': 'volkov@petcare.ru', 'first_name': 'Сергей',
                'last_name': 'Волков', 'phone': '+7-999-555-55-55',
                'specialties': ['Стоматология'],
                'experience': 5, 'education': 'Казанская ГАВМ',
                'bio': 'Ветеринарный стоматолог. Чистка, лечение и удаление зубов.',
                'consultation_price': '1500.00',
            },
        ]

        doctors = []
        for d in doctors_data:
            user, created = User.objects.get_or_create(
                email=d['email'],
                defaults={
                    'first_name': d['first_name'],
                    'last_name': d['last_name'],
                    'phone': d['phone'],
                    'role': 'veterinarian',
                },
            )
            if created:
                user.set_password('doctor123')
                user.save()

            doctor, _ = Doctor.objects.get_or_create(
                user=user,
                defaults={
                    'experience_years': d['experience'],
                    'education': d['education'],
                    'bio': d['bio'],
                    'consultation_price': Decimal(d['consultation_price']),
                },
            )
            for sp_name in d['specialties']:
                doctor.specialties.add(specs[sp_name])
            doctors.append(doctor)

        self.stdout.write(f'  Ветеринары: {len(doctors)}')

        # ─── Расписание ─────────────────────────
        for doctor in doctors:
            if not Schedule.objects.filter(doctor=doctor).exists():
                for day in range(0, 5):  # Пн-Пт
                    Schedule.objects.create(
                        doctor=doctor,
                        day_of_week=day,
                        start_time=time(9, 0),
                        end_time=time(18, 0),
                        slot_duration=30,
                    )
                Schedule.objects.create(
                    doctor=doctor,
                    day_of_week=5,  # Суббота
                    start_time=time(10, 0),
                    end_time=time(15, 0),
                    slot_duration=30,
                )

        self.stdout.write('  Расписание создано')

        # ─── Услуги ─────────────────────────────
        services_data = [
            ('Первичный осмотр', 'Терапия', 30, '1500.00',
             'Полный осмотр животного с назначением лечения'),
            ('Повторный осмотр', 'Терапия', 20, '1000.00',
             'Контрольный осмотр после лечения'),
            ('Вакцинация', 'Терапия', 15, '800.00',
             'Плановая вакцинация с оформлением паспорта'),
            ('УЗИ', 'Терапия', 40, '2500.00',
             'Ультразвуковое исследование внутренних органов'),
            ('ЭКГ', 'Кардиология', 30, '2000.00',
             'Электрокардиография для диагностики сердечных заболеваний'),
            ('Кастрация кота', 'Хирургия', 60, '3500.00',
             'Операция по кастрации с анестезией'),
            ('Стерилизация кошки', 'Хирургия', 90, '5500.00',
             'Операция по стерилизации с анестезией'),
            ('Удаление новообразований', 'Хирургия', 120, '8000.00',
             'Хирургическое удаление опухолей и новообразований'),
            ('Осмотр глазного дна', 'Офтальмология', 30, '1800.00',
             'Офтальмоскопия и диагностика заболеваний глаз'),
            ('Лечение конъюнктивита', 'Офтальмология', 20, '1200.00',
             'Диагностика и лечение воспалительных заболеваний глаз'),
            ('Лечение дерматита', 'Дерматология', 30, '2000.00',
             'Диагностика и лечение кожных заболеваний'),
            ('Трихоскопия', 'Дерматология', 25, '1500.00',
             'Исследование шерсти и кожного покрова'),
            ('Чистка зубов', 'Стоматология', 45, '3000.00',
             'Ультразвуковая чистка зубов с полировкой'),
            ('Удаление зуба', 'Стоматология', 30, '2000.00',
             'Удаление молочных или постоянных зубов'),
        ]

        services = []
        for name, spec_name, duration, price, desc in services_data:
            svc, _ = Service.objects.get_or_create(
                name=name,
                defaults={
                    'specialty': specs[spec_name],
                    'duration_minutes': duration,
                    'price': Decimal(price),
                    'description': desc,
                },
            )
            services.append(svc)

        self.stdout.write(f'  Услуги: {len(services)}')

        # ─── Клиент и питомцы ───────────────────
        client, created = User.objects.get_or_create(
            email='client@example.com',
            defaults={
                'first_name': 'Мария',
                'last_name': 'Смирнова',
                'phone': '+7-999-000-00-00',
                'role': 'client',
            },
        )
        if created:
            client.set_password('client123')
            client.save()

        pets_data = [
            ('Барсик', 'cat', 'Британская', 36, '5.20', 'Аллергия на курицу'),
            ('Рекс', 'dog', 'Немецкая овчарка', 48, '32.00', ''),
            ('Кеша', 'bird', 'Волнистый попугай', 12, '0.04', ''),
        ]

        pets = []
        for name, species, breed, age, weight, notes in pets_data:
            pet, _ = Pet.objects.get_or_create(
                owner=client, name=name,
                defaults={
                    'species': species,
                    'breed': breed,
                    'age': age,
                    'weight': Decimal(weight),
                    'health_notes': notes,
                },
            )
            pets.append(pet)

        self.stdout.write(f'  Питомцы: {len(pets)}')

        # ─── Записи на приём ────────────────────
        today = timezone.now().date()
        if not Appointment.objects.filter(client=client).exists():
            # Завершённая запись (вчера)
            appt1 = Appointment.objects.create(
                client=client,
                doctor=doctors[0],
                pet=pets[0],
                service=services[0],
                date=today - timedelta(days=1),
                time_slot=time(10, 0),
                status='completed',
            )

            # Подтверждённая запись (завтра)
            appt2 = Appointment.objects.create(
                client=client,
                doctor=doctors[1],
                pet=pets[1],
                service=services[5],
                date=today + timedelta(days=1),
                time_slot=time(14, 0),
                status='confirmed',
            )

            # Ожидающая запись (через 3 дня)
            appt3 = Appointment.objects.create(
                client=client,
                doctor=doctors[3],
                pet=pets[0],
                service=services[10],
                date=today + timedelta(days=3),
                time_slot=time(11, 30),
                status='pending',
            )

            self.stdout.write('  Записи: 3')

            # ─── Отзыв ──────────────────────────
            Review.objects.get_or_create(
                appointment=appt1,
                defaults={
                    'author': client,
                    'doctor': doctors[0],
                    'rating': 5,
                    'text': 'Отличный врач! Барсику стало значительно лучше после лечения. '
                            'Алексей Иванович очень внимательный и профессиональный.',
                    'is_approved': True,
                },
            )
            self.stdout.write('  Отзывы: 1')

        # ─── Админ ──────────────────────────────
        admin, created = User.objects.get_or_create(
            email='admin@petcare.ru',
            defaults={
                'first_name': 'Админ',
                'last_name': 'Петкеа',
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True,
            },
        )
        if created:
            admin.set_password('admin123')
            admin.save()
            self.stdout.write('  Администратор создан')

        self.stdout.write(self.style.SUCCESS('\nГотово! Тестовые данные загружены.'))
        self.stdout.write(f'\nДанные для входа:')
        self.stdout.write(f'  Клиент:  client@example.com / client123')
        self.stdout.write(f'  Врач:    ivanov@petcare.ru / doctor123')
        self.stdout.write(f'  Админ:   admin@petcare.ru / admin123')
