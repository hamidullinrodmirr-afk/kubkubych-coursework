# КубКубыч — интернет-магазин конструкторов LEGO

Курсовой проект по дисциплине «Веб-технологии».

**Автор:** Хамидуллин Радмир Робертович, группа 241-672.

«КубКубыч» — полнофункциональное веб-приложение интернет-магазина LEGO-наборов на Django и
Django REST Framework: каталог с фильтрами, корзина, оформление заказа, личный кабинет, роли
покупателя и администратора, отзывы только после покупки, избранное, REST API и серверный
HTML-интерфейс.

## Стек

Python 3.11+, Django 5, Django REST Framework, SimpleJWT, django-filter, PostgreSQL / SQLite,
Redis, Celery + Celery Beat, Mailhog, Sentry, Django Silk, OAuth2 (Google / VK), Docker Compose,
Pillow, gunicorn, nginx.

## Что реализовано

- каталог наборов с поиском, сортировкой и фильтрами по серии, цене, возрасту, количеству деталей,
  наличию, скидке и рейтингу;
- аннотации queryset: средний рейтинг, число отзывов, продажи и добавления в избранное;
- избранное с признаком `is_favorite` через context сериализатора (без N+1);
- корзина с контролем остатка, изменением количества, очисткой и сводкой;
- атомарное оформление заказа: блокировка корзины, повторная проверка остатка, снимок состава,
  уменьшение остатка, очистка корзины и письмо через Celery;
- статусная модель заказа (`new → processing → shipped → delivered`, отмена) с возвратом остатка;
- отзывы только на купленный и доставленный набор, модерация и повторная модерация после правки;
- роли покупателя и администратора, блокировка и смена роли, JWT + OAuth2;
- администраторская аналитика: продажи, популярность, пользователи, низкий остаток;
- настройки магазина (SiteSetting), Django Admin, Postman-коллекция, автотесты;
- Celery Beat: автоотмена «зависших» заказов, ежедневный отчёт о продажах, отчёт о низком остатке.

## Локальный запуск без Docker

```bash
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux / macOS
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_store
python manage.py runserver
```

Сайт: <http://127.0.0.1:8000/>. Без переменных окружения используется SQLite.

## Запуск через Docker

```bash
cp .env.docker.example .env.docker
docker compose up --build
```

Поднимаются сервисы: `web` (Django + gunicorn), `db` (PostgreSQL), `redis`, `celery`,
`celery-beat`, `mailhog`, `nginx`. После старта выполните наполнение данными:

```bash
docker compose exec web python manage.py seed_store
```

Адреса: сайт — <http://127.0.0.1:8000/>, nginx — <http://127.0.0.1/>, Mailhog —
<http://127.0.0.1:8025/>.

## Демо-аккаунты

| Роль          | Email                  | Пароль       |
|---------------|------------------------|--------------|
| Администратор | admin@kubkubych.ru     | admin123     |
| Покупатель    | buyer@kubkubych.ru     | buyer123     |
| Покупатель    | collector@kubkubych.ru | collector123 |

## Основные API-эндпоинты

- Аутентификация: `POST /api/auth/register/`, `POST /api/auth/login/`, `POST /api/auth/refresh/`,
  `POST /api/auth/logout/`, `GET|PATCH /api/auth/me/`, `GET /api/auth/oauth/google/`, `.../vk/`.
- Пользователи (admin): `GET /api/users/`, `GET /api/users/{id}/`,
  `PATCH /api/users/{id}/role|block|unblock/`.
- Категории: `GET /api/categories/`, CRUD для администратора.
- Товары: `GET /api/products/`, `GET /api/products/{id}/`, `POST|PATCH|DELETE` (admin),
  `POST|DELETE /api/products/{id}/favorite/`, `GET /api/products/popular/`,
  `GET /api/products/discounts/`, `GET /api/products/{id}/reviews/`.
- Корзина: `GET|POST /api/cart/items/`, `PATCH|DELETE /api/cart/items/{id}/`,
  `DELETE /api/cart/clear/`, `GET /api/cart/summary/`.
- Заказы: `GET|POST /api/orders/`, `GET /api/orders/{id}/`, `POST /api/orders/{id}/cancel/`,
  `PATCH /api/orders/{id}/status/` (admin).
- Отзывы: `GET|POST /api/reviews/`, `PATCH|DELETE /api/reviews/{id}/`,
  `PATCH /api/reviews/{id}/moderate/` (admin).
- Аналитика (admin): `GET /api/analytics/sales|products|users|low-stock/`.
- Настройки магазина: `GET /api/settings/`, `PATCH` (admin).
- Служебное: `GET /api/health/`, `GET /api/debug/sentry-test/` (только при DEBUG).

## Postman

Коллекция: `postman/KubKubych_API.postman_collection.json`.

1. Импортируйте файл в Postman (Import → File).
2. Откройте папку **Auth → Login** и выполните запрос — токен сохранится в переменную
   `access_token` автоматически (см. вкладку Tests). По умолчанию вход под администратором.
3. Остальные запросы используют bearer-токен из переменной коллекции. При создании корзины,
   заказа и отзыва соответствующие `*_id` сохраняются автоматически.

Переменная `base_url` по умолчанию `http://127.0.0.1:8000`.

## Тесты

```bash
python manage.py test
```

Покрыто 53 сценария: регистрация и блокировка, JWT, каталог и аннотации, фильтры, отсутствие
N+1, корзина, атомарное оформление, права доступа к заказам, переходы статусов, отзывы и
модерация, доступ к аналитике, healthcheck.

## Мониторинг и почта

- **Mailhog** — письма заказов и отчёты: <http://127.0.0.1:8025/>.
- **Django Silk** (только при `DEBUG=True`) — профилирование SQL: <http://127.0.0.1:8000/silk/>.
  Позволяет увидеть число запросов и проверить работу `select_related` / `prefetch_related`.
- **Sentry** — подключается только при заданном `SENTRY_DSN`; без него запуск не ломается.
- **Django Admin** — <http://127.0.0.1:8000/admin/>.

## Что показать на защите

- бизнес-логика интернет-магазина реализована полностью, без заглушек;
- заказ создаётся атомарно (`transaction.atomic`, `select_for_update`), остаток проверяется на
  уровне корзины и повторно перед списанием;
- отзыв можно оставить только после доставленного заказа, публично видны лишь одобренные;
- права доступа разделены по ролям и проверяются на уровне queryset и объекта;
- `select_related` / `prefetch_related` и аннотации убирают N+1 — видно в Silk;
- `SerializerMethodField` и context используются для вычисляемых полей и признака избранного;
- Celery отвечает за письма и периодические задачи (автоотмена, ежедневный и складской отчёты).
