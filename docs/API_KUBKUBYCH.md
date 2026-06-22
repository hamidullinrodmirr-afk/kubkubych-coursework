# API интернет-магазина «КубКубыч»

Базовый адрес: `http://127.0.0.1:8000/api/`. Защищённые запросы используют заголовок
`Authorization: Bearer <access_token>`.

## Покупатель

| Метод | Маршрут | Назначение |
| --- | --- | --- |
| POST | `/auth/register/` | Регистрация |
| POST | `/auth/login/` | Получение JWT |
| POST | `/auth/refresh/` | Обновление access-токена |
| POST | `/auth/logout/` | Отзыв refresh-токена (blacklist) |
| GET/PATCH | `/auth/me/` | Профиль |
| GET | `/categories/` | Активные серии |
| GET | `/products/` | Каталог и фильтры |
| GET | `/products/{id}/` | Карточка набора |
| GET | `/products/popular/`, `/products/discounts/` | Подборки |
| GET | `/products/{id}/reviews/` | Одобренные отзывы набора |
| POST/DELETE | `/products/{id}/favorite/` | Избранное |
| GET | `/products/favorites/` | Мои избранные наборы |
| GET/POST | `/cart/items/` | Корзина |
| PATCH/DELETE | `/cart/items/{id}/` | Изменение и удаление строки |
| DELETE | `/cart/clear/` | Очистка корзины |
| GET | `/cart/summary/` | Свод по корзине |
| GET/POST | `/orders/` | История и оформление заказов |
| GET | `/orders/{id}/` | Детали своего заказа |
| POST | `/orders/{id}/cancel/` | Отмена заказа |
| GET/POST | `/reviews/` | Отзывы |
| PATCH/DELETE | `/reviews/{id}/` | Правка и удаление своего отзыва |

Пример оформления заказа:

```json
{
  "recipient_name": "Радмир Хамидуллин",
  "recipient_phone": "+79990000000",
  "city": "Москва",
  "street": "Тверская",
  "house": "7",
  "apartment": "34",
  "postal_code": "101000",
  "payment_method": "card_on_delivery",
  "comment": "Позвонить за час до доставки"
}
```

Способы оплаты: `cash`, `card_on_delivery`, `online_mock`. Индекс — ровно 6 цифр,
сумма заказа — от 500 до 100 000 ₽.

## Администратор

Управление наборами и сериями — обычными `POST`, `PATCH`, `DELETE` на `/products/` и
`/categories/`. Дополнительно:

| Метод | Маршрут | Назначение |
| --- | --- | --- |
| GET | `/users/` | Список пользователей (фильтры `role`, `is_active`, `search`) |
| GET | `/users/{id}/` | Карточка пользователя |
| PATCH | `/users/{id}/role/` | Смена роли |
| PATCH | `/users/{id}/block/`, `/users/{id}/unblock/` | Блокировка и разблокировка |
| PATCH | `/orders/{id}/status/` | Переход статуса заказа |
| PATCH | `/reviews/{id}/moderate/` | Модерация отзыва |
| GET | `/analytics/sales/`, `/products/`, `/users/`, `/low-stock/` | Аналитика |
| GET/PATCH | `/settings/` | Настройки магазина |

Статусы заказа переходят последовательно: `new → processing → shipped → delivered`.
Отменить (`cancelled`) можно новый или обрабатываемый заказ — остаток возвращается на склад.
