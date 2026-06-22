# API интернет-магазина «КубКубыч»

Базовый адрес: `http://127.0.0.1:8000/api/`. Защищённые запросы используют заголовок `Authorization: Bearer <access_token>`.

## Покупатель

| Метод | Маршрут | Назначение |
| --- | --- | --- |
| POST | `/auth/register/` | Регистрация |
| POST | `/auth/login/` | Получение JWT |
| GET/PATCH | `/auth/me/` | Профиль |
| GET | `/products/` | Каталог и фильтры |
| GET | `/products/{id}/` | Карточка набора |
| POST/DELETE | `/products/{id}/favorite/` | Избранное |
| GET/POST | `/cart/items/` | Корзина |
| PATCH/DELETE | `/cart/items/{id}/` | Изменение строки корзины |
| GET/POST | `/orders/` | История и оформление заказов |
| GET | `/orders/{id}/` | Детали своего заказа |
| GET/POST | `/reviews/` | Отзывы |

Пример оформления заказа:

```json
{
  "recipient_name": "Радмир Хамидуллин",
  "phone": "+79990000000",
  "delivery_address": "Москва, ул. Примерная, 10, 101000",
  "payment_method": "card"
}
```

## Администратор

Администратор управляет наборами через обычные `POST`, `PATCH` и `DELETE` на `/products/`. Также ему доступны:

| Метод | Маршрут | Назначение |
| --- | --- | --- |
| GET | `/auth/users/` | Список пользователей |
| PATCH | `/auth/users/{id}/block/` | Блокировка/разблокировка |
| PATCH | `/orders/{id}/status/` | Переход статуса заказа |
| PATCH | `/reviews/{id}/moderate/` | Модерация отзыва |

Статусы заказа переходят только последовательно: `new → processing → shipped → delivered`. Отменить можно новый или обрабатываемый заказ.
