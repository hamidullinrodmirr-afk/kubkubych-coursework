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
                'bio': 'Опытный терапевт и кардиолог. Специализируется на лечении собак и кошек. '
                       'Регулярно повышает квалификацию на международных конференциях.',
                'consultation_price': '2000.00',
                'photo': 'https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?w=400&h=400&fit=crop',
            },
            {
                'email': 'petrova@petcare.ru', 'first_name': 'Елена',
                'last_name': 'Петрова', 'phone': '+7-999-222-22-22',
                'specialties': ['Хирургия'],
                'experience': 8, 'education': 'РУДН, ветеринарный факультет',
                'bio': 'Хирург высшей категории. Проводит операции любой сложности, '
                       'включая ортопедические и абдоминальные вмешательства.',
                'consultation_price': '2500.00',
                'photo': 'https://images.unsplash.com/photo-1559839734-2b71ea197ec2?w=400&h=400&fit=crop',
            },
            {
                'email': 'sidorov@petcare.ru', 'first_name': 'Дмитрий',
                'last_name': 'Сидоров', 'phone': '+7-999-333-33-33',
                'specialties': ['Офтальмология', 'Терапия'],
                'experience': 6, 'education': 'СПбГАВМ',
                'bio': 'Специалист по заболеваниям глаз у домашних животных. '
                       'Владеет современными методами диагностики и микрохирургии глаза.',
                'consultation_price': '1800.00',
                'photo': 'https://images.unsplash.com/photo-1622253692010-333f2da6031d?w=400&h=400&fit=crop',
            },
            {
                'email': 'kuznetsova@petcare.ru', 'first_name': 'Анна',
                'last_name': 'Кузнецова', 'phone': '+7-999-444-44-44',
                'specialties': ['Дерматология', 'Терапия'],
                'experience': 10, 'education': 'МГАВМиБ им. Скрябина',
                'bio': 'Дерматолог с большим опытом лечения аллергий и кожных заболеваний. '
                       'Применяет комплексный подход к диагностике и лечению.',
                'consultation_price': '2200.00',
                'photo': 'https://images.unsplash.com/photo-1594824476967-48c8b964ac31?w=400&h=400&fit=crop',
            },
            {
                'email': 'volkov@petcare.ru', 'first_name': 'Сергей',
                'last_name': 'Волков', 'phone': '+7-999-555-55-55',
                'specialties': ['Стоматология'],
                'experience': 5, 'education': 'Казанская ГАВМ',
                'bio': 'Ветеринарный стоматолог. Чистка, лечение и удаление зубов. '
                       'Безболезненные процедуры с использованием современного оборудования.',
                'consultation_price': '1500.00',
                'photo': 'https://images.unsplash.com/photo-1537368910025-700350fe46c7?w=400&h=400&fit=crop',
            },
            {
                'email': 'morozova@petcare.ru', 'first_name': 'Ольга',
                'last_name': 'Морозова', 'phone': '+7-999-666-66-66',
                'specialties': ['Кардиология', 'Хирургия'],
                'experience': 15, 'education': 'МГАВМиБ им. Скрябина',
                'bio': 'Кардиохирург с 15-летним стажем. Специализируется на диагностике и '
                       'хирургическом лечении врождённых и приобретённых пороков сердца у животных. '
                       'Автор научных публикаций по ветеринарной кардиологии.',
                'consultation_price': '3000.00',
                'photo': 'https://images.unsplash.com/photo-1651008376811-b90baee60c1f?w=400&h=400&fit=crop',
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
            # Обновляем фото (URL), даже если врач уже существовал
            if d.get('photo') and not doctor.photo_url:
                doctor.photo_url = d['photo']
                doctor.save(update_fields=['photo_url'])
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

        # ─── Клиенты и питомцы ─────────────────
        # Клиент 1 — Мария Смирнова
        client1, created = User.objects.get_or_create(
            email='client@example.com',
            defaults={
                'first_name': 'Мария',
                'last_name': 'Смирнова',
                'phone': '+7-999-000-00-00',
                'role': 'client',
            },
        )
        if created:
            client1.set_password('client123')
            client1.save()

        pets_client1 = []
        pets_data_1 = [
            ('Барсик', 'cat', 'Британская короткошёрстная', 36, '5.20', 'Аллергия на курицу'),
            ('Рекс', 'dog', 'Немецкая овчарка', 48, '32.00', 'Прививки актуальны до 2027 г.'),
            ('Кеша', 'bird', 'Волнистый попугай', 12, '0.04', ''),
        ]
        for name, species, breed, age, weight, notes in pets_data_1:
            pet, _ = Pet.objects.get_or_create(
                owner=client1, name=name,
                defaults={
                    'species': species,
                    'breed': breed,
                    'age': age,
                    'weight': Decimal(weight),
                    'health_notes': notes,
                },
            )
            pets_client1.append(pet)

        # Клиент 2 — Игорь Петров
        client2, created = User.objects.get_or_create(
            email='petrov@mail.ru',
            defaults={
                'first_name': 'Игорь',
                'last_name': 'Петров',
                'phone': '+7-999-777-77-77',
                'role': 'client',
            },
        )
        if created:
            client2.set_password('client123')
            client2.save()

        pets_client2 = []
        pets_data_2 = [
            ('Мурка', 'cat', 'Шотландская вислоухая', 24, '4.10',
             'Склонность к мочекаменной болезни'),
            ('Бобик', 'dog', 'Лабрадор-ретривер', 60, '28.50',
             'Хромота на левую заднюю лапу'),
        ]
        for name, species, breed, age, weight, notes in pets_data_2:
            pet, _ = Pet.objects.get_or_create(
                owner=client2, name=name,
                defaults={
                    'species': species,
                    'breed': breed,
                    'age': age,
                    'weight': Decimal(weight),
                    'health_notes': notes,
                },
            )
            pets_client2.append(pet)

        all_pets = pets_client1 + pets_client2
        self.stdout.write(f'  Питомцы: {len(all_pets)}')

        # ─── Записи на приём ────────────────────
        today = timezone.now().date()
        appointments_created = 0

        if not Appointment.objects.filter(client=client1).exists():
            # Завершённые записи (прошлые даты) — клиент 1
            appt1 = Appointment.objects.create(
                client=client1,
                doctor=doctors[0],  # Иванов — терапия
                pet=pets_client1[0],  # Барсик
                service=services[0],  # Первичный осмотр
                date=today - timedelta(days=14),
                time_slot=time(10, 0),
                status='completed',
                comment='Жалобы на снижение аппетита.',
            )
            appt2 = Appointment.objects.create(
                client=client1,
                doctor=doctors[1],  # Петрова — хирургия
                pet=pets_client1[0],  # Барсик
                service=services[5],  # Кастрация кота
                date=today - timedelta(days=7),
                time_slot=time(9, 0),
                status='completed',
                comment='Плановая кастрация, подготовка — голодная диета 12 часов.',
            )
            appt3 = Appointment.objects.create(
                client=client1,
                doctor=doctors[3],  # Кузнецова — дерматология
                pet=pets_client1[0],  # Барсик
                service=services[10],  # Лечение дерматита
                date=today - timedelta(days=5),
                time_slot=time(11, 30),
                status='completed',
                comment='Покраснение на животе, зуд.',
            )
            appt4 = Appointment.objects.create(
                client=client1,
                doctor=doctors[4],  # Волков — стоматология
                pet=pets_client1[1],  # Рекс
                service=services[12],  # Чистка зубов
                date=today - timedelta(days=3),
                time_slot=time(15, 0),
                status='completed',
                comment='Плановая чистка зубов, зубной камень.',
            )

            # Подтверждённая запись (завтра) — клиент 1
            appt5 = Appointment.objects.create(
                client=client1,
                doctor=doctors[2],  # Сидоров — офтальмология
                pet=pets_client1[0],  # Барсик
                service=services[8],  # Осмотр глазного дна
                date=today + timedelta(days=1),
                time_slot=time(14, 0),
                status='confirmed',
                comment='Слезотечение из правого глаза.',
            )

            # Ожидающая запись (через 5 дней) — клиент 1
            appt6 = Appointment.objects.create(
                client=client1,
                doctor=doctors[0],  # Иванов — терапия
                pet=pets_client1[1],  # Рекс
                service=services[2],  # Вакцинация
                date=today + timedelta(days=5),
                time_slot=time(10, 30),
                status='pending',
                comment='Плановая ежегодная вакцинация.',
            )

            # Отменённая запись — клиент 1
            appt7 = Appointment.objects.create(
                client=client1,
                doctor=doctors[5],  # Морозова — кардиология
                pet=pets_client1[1],  # Рекс
                service=services[4],  # ЭКГ
                date=today - timedelta(days=2),
                time_slot=time(12, 0),
                status='cancelled',
                cancel_reason='Клиент заболел, перенос на другую дату.',
            )

            appointments_created += 7

            # ─── Отзывы от клиента 1 ──────────────
            Review.objects.get_or_create(
                appointment=appt1,
                defaults={
                    'author': client1,
                    'doctor': doctors[0],
                    'rating': 5,
                    'text': 'Отличный врач! Барсику стало значительно лучше после лечения. '
                            'Алексей Иванович очень внимательный и профессиональный. '
                            'Подробно объяснил причину плохого аппетита и назначил эффективное лечение.',
                    'is_approved': True,
                },
            )
            Review.objects.get_or_create(
                appointment=appt2,
                defaults={
                    'author': client1,
                    'doctor': doctors[1],
                    'rating': 5,
                    'text': 'Елена Петрова провела кастрацию Барсика очень аккуратно. '
                            'Операция прошла без осложнений, кот быстро восстановился. '
                            'Отдельное спасибо за подробные инструкции по уходу после операции.',
                    'is_approved': True,
                },
            )
            Review.objects.get_or_create(
                appointment=appt3,
                defaults={
                    'author': client1,
                    'doctor': doctors[3],
                    'rating': 4,
                    'text': 'Анна Кузнецова — грамотный специалист. Быстро определила причину '
                            'дерматита у Барсика и назначила лечение. Единственный минус — '
                            'пришлось подождать в очереди около 20 минут, хотя записывались заранее.',
                    'is_approved': True,
                },
            )
            Review.objects.get_or_create(
                appointment=appt4,
                defaults={
                    'author': client1,
                    'doctor': doctors[4],
                    'rating': 4,
                    'text': 'Рексу почистили зубы ультразвуком. Сергей Волков работает '
                            'аккуратно, собака перенесла процедуру спокойно. Результат '
                            'отличный — зубной камень полностью удалён. Рекомендую!',
                    'is_approved': True,
                },
            )

        if not Appointment.objects.filter(client=client2).exists():
            # Завершённые записи — клиент 2
            appt8 = Appointment.objects.create(
                client=client2,
                doctor=doctors[0],  # Иванов — терапия
                pet=pets_client2[0],  # Мурка
                service=services[0],  # Первичный осмотр
                date=today - timedelta(days=10),
                time_slot=time(11, 0),
                status='completed',
                comment='Первичный осмотр, жалобы на вялость.',
            )
            appt9 = Appointment.objects.create(
                client=client2,
                doctor=doctors[5],  # Морозова — кардиология
                pet=pets_client2[1],  # Бобик
                service=services[4],  # ЭКГ
                date=today - timedelta(days=6),
                time_slot=time(13, 0),
                status='completed',
                comment='Контрольное ЭКГ, шум в сердце.',
            )
            appt10 = Appointment.objects.create(
                client=client2,
                doctor=doctors[2],  # Сидоров — офтальмология
                pet=pets_client2[0],  # Мурка
                service=services[9],  # Лечение конъюнктивита
                date=today - timedelta(days=4),
                time_slot=time(16, 0),
                status='completed',
                comment='Покраснение и выделения из левого глаза.',
            )

            # Подтверждённая запись (через 2 дня) — клиент 2
            Appointment.objects.create(
                client=client2,
                doctor=doctors[1],  # Петрова — хирургия
                pet=pets_client2[1],  # Бобик
                service=services[7],  # Удаление новообразований
                date=today + timedelta(days=2),
                time_slot=time(9, 30),
                status='confirmed',
                comment='Небольшое образование на правом боку, рекомендовано удаление.',
            )

            # Ожидающая запись (через 7 дней) — клиент 2
            Appointment.objects.create(
                client=client2,
                doctor=doctors[3],  # Кузнецова — дерматология
                pet=pets_client2[0],  # Мурка
                service=services[11],  # Трихоскопия
                date=today + timedelta(days=7),
                time_slot=time(10, 0),
                status='pending',
                comment='Выпадение шерсти на спине.',
            )

            # Подтверждённая запись на послезавтра — клиент 2
            Appointment.objects.create(
                client=client2,
                doctor=doctors[0],  # Иванов — терапия
                pet=pets_client2[0],  # Мурка
                service=services[1],  # Повторный осмотр
                date=today + timedelta(days=4),
                time_slot=time(14, 30),
                status='confirmed',
                comment='Контрольный осмотр после лечения.',
            )

            appointments_created += 6

            # ─── Отзывы от клиента 2 ──────────────
            Review.objects.get_or_create(
                appointment=appt8,
                defaults={
                    'author': client2,
                    'doctor': doctors[0],
                    'rating': 5,
                    'text': 'Обратились к Алексею Иванову с Муркой — кошка была вялой и '
                            'плохо ела. Врач провёл тщательный осмотр, взял анализы. '
                            'Диагноз поставили быстро, лечение помогло уже через два дня. '
                            'Очень благодарны!',
                    'is_approved': True,
                },
            )
            Review.objects.get_or_create(
                appointment=appt9,
                defaults={
                    'author': client2,
                    'doctor': doctors[5],
                    'rating': 4,
                    'text': 'Ольга Морозова — отличный кардиолог. Провела ЭКГ Бобику, '
                            'всё подробно объяснила. Обнаружила небольшой шум в сердце, '
                            'назначила поддерживающую терапию. Единственное — хотелось бы '
                            'более подробную распечатку результатов.',
                    'is_approved': True,
                },
            )
            Review.objects.get_or_create(
                appointment=appt10,
                defaults={
                    'author': client2,
                    'doctor': doctors[2],
                    'rating': 3,
                    'text': 'Дмитрий Сидоров осмотрел Мурку и назначил капли от '
                            'конъюнктивита. Лечение в целом помогло, но пришлось прийти '
                            'повторно — первый курс капель оказался недостаточным. '
                            'Хотелось бы более точного назначения с первого раза.',
                    'is_approved': True,
                },
            )

        total_appointments = Appointment.objects.count()
        total_reviews = Review.objects.count()
        self.stdout.write(f'  Записи на приём: {total_appointments}')
        self.stdout.write(f'  Отзывы: {total_reviews}')

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
        self.stdout.write(f'  Клиент 1: client@example.com / client123')
        self.stdout.write(f'  Клиент 2: petrov@mail.ru / client123')
        self.stdout.write(f'  Врач:     ivanov@petcare.ru / doctor123')
        self.stdout.write(f'  Админ:    admin@petcare.ru / admin123')
