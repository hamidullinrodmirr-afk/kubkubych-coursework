# PetCare — Веб-приложение ветеринарной клиники

Курсовой проект по дисциплине «Веб-технологии».
**Автор:** Закс Дмитрий Александрович, группа 241-671

## Стек технологий

- **Backend:** Django 5.2, Django REST Framework
- **База данных:** PostgreSQL (SQLite для локальной разработки)
- **Аутентификация:** JWT (SimpleJWT), OAuth2 (Google, VKontakte)
- **Фоновые задачи:** Celery + Redis
- **Email:** Mailhog (dev), SMTP (prod)
- **Контейнеризация:** Docker Compose
- **Frontend:** Django Templates + Vanilla JS

## Быстрый старт (локальная разработка)

```bash
# Клонирование
git clone https://github.com/Qikit/petcare-backend.git
cd petcare-backend

# Виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate   # Windows

# Зависимости
pip install -r requirements.txt

# Миграции и тестовые данные
python manage.py migrate
python manage.py seed_data

# Запуск
python manage.py runserver
```

Откройте http://127.0.0.1:8000/

### Тестовые учётные записи

| Роль | Email | Пароль |
|------|-------|--------|
| Клиент | client@example.com | client123 |
| Ветеринар | ivanov@petcare.ru | doctor123 |
| Администратор | admin@petcare.ru | admin123 |

## Запуск через Docker

```bash
cp .env.docker.example .env.docker
docker-compose up --build
```

Сервисы:
- Приложение: http://localhost (Nginx) или http://localhost:8000 (Django)
- Админка: http://localhost/admin/
- Mailhog (почта): http://localhost:8025

## Запуск тестов

```bash
python manage.py test
```

## Структура проекта

```
petcare/          — настройки Django, Celery, маршрутизация
users/            — пользователи, аутентификация, OAuth2
pets/             — CRUD питомцев
doctors/          — врачи, специализации, расписание
services/         — каталог услуг
appointments/     — записи на приём, медкарты, фоновые задачи
reviews/          — отзывы с модерацией
templates/        — HTML-шаблоны фронтенда
static/           — CSS, JavaScript
nginx/            — конфигурация Nginx
docs/             — техническое задание
```

## API эндпоинты

| Метод | URL | Описание |
|-------|-----|----------|
| POST | /api/auth/register/ | Регистрация |
| POST | /api/auth/login/ | Получение JWT |
| POST | /api/auth/refresh/ | Обновление токена |
| GET/PATCH | /api/auth/me/ | Профиль пользователя |
| GET/POST | /api/pets/ | Питомцы |
| GET | /api/doctors/ | Список врачей |
| GET | /api/doctors/{id}/ | Детали врача |
| GET | /api/doctors/{id}/available-slots/ | Свободные слоты |
| GET | /api/services/ | Каталог услуг |
| GET/POST | /api/appointments/ | Записи на приём |
| POST | /api/appointments/{id}/cancel/ | Отмена записи |
| GET/POST | /api/reviews/ | Отзывы |
| GET | /api/auth/oauth/google/ | OAuth Google |
| GET | /api/auth/oauth/vk/ | OAuth VKontakte |

## OAuth2 настройка

Для работы OAuth2 добавьте в `.env`:

```
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
VK_CLIENT_ID=your_vk_app_id
VK_CLIENT_SECRET=your_vk_secret_key
```
