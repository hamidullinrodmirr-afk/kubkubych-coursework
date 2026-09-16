# Отчёт по лабораторной работе 1
## Проектирование базы данных интернет-магазина «КубКубыч»

### Цель работы
Определить предметную область, роли пользователей, состав сущностей и связи базы данных веб-приложения интернет-магазина конструкторов.

### Анализ предметной области
Основной объект каталога — набор конструктора. Набор относится к серии, имеет уникальный артикул, описание, возрастные характеристики, количество деталей, цену, скидку и остаток. Покупка включает выбор товаров, формирование корзины, оформление заказа и обработку его статуса. Отзыв связан с приобретённым товаром и проходит модерацию.

Посетитель просматривает публичный каталог. Покупатель дополнительно использует корзину, избранное, заказы и отзывы. Администратор управляет каталогом, пользователями, заказами, модерацией и настройками витрины.

### Анализ аналогов
Официальный магазин LEGO: [страница выбора товаров](https://www.lego.com/en-us/categories/shop-by). На публичной странице представлены способы выбора наборов по теме и возрасту. Для проекта это обосновывает выделение серии и хранение возрастных характеристик. Типы страниц аналога — каталог и тематические/возрастные подборки. Публичный интерфейс административной части не исследовался; её функции и внутренние таблицы не выводятся из устройства сайта.

Brickset: [каталог наборов](https://brickset.com/sets). Публичный интерфейс содержит поиск, переход к расширенному поиску, списки тем и годов, а также тематические подборки. Для проекта значимы идентификация наборов, классификация и поиск. Brickset используется как аналог каталога, а не как подтверждение реализации процесса оформления заказа.

Вывод из сравнения: каталогу необходимы самостоятельные сущности серии и товара, идентификатор товара и средства поиска. Корзина, заказ и отзыв определены уже процессами собственного интернет-магазина. Внутренние схемы БД аналогов неизвестны; приведённое сравнение относится к наблюдаемой функциональности.

### Инфологическая модель
| Сущность | Содержание | Связи |
| --- | --- | --- |
| User | Учётная запись и роль | Заказы, корзина, избранное, отзывы |
| Category | Серия набора | Одна серия содержит несколько товаров |
| Product | Характеристики и остаток | Серия, позиции заказов, корзина, отзывы |
| Favorite | Добавление в избранное | Пользователь и товар |
| CartItem | Товар и количество в корзине | Пользователь и товар |
| Order | Доставка, оплата, статус и сумма | Пользователь и позиции заказа |
| OrderItem | Снимок состава покупки | Заказ и товар |
| Review | Оценка, текст, модерация | Автор и товар |
| SiteSetting | Контакты и тексты магазина | Самостоятельная одиночная запись |

~~~mermaid
erDiagram
    USER ||--o{ ORDER : creates
    USER ||--o{ CART_ITEM : owns
    USER ||--o{ FAVORITE : marks
    USER ||--o{ REVIEW : writes
    CATEGORY ||--o{ PRODUCT : contains
    PRODUCT ||--o{ CART_ITEM : selected
    PRODUCT ||--o{ FAVORITE : selected
    PRODUCT ||--o{ ORDER_ITEM : purchased
    PRODUCT ||--o{ REVIEW : receives
    ORDER ||--o{ ORDER_ITEM : contains
~~~

Диаграмма показывает ограничения связей моделей. Отдельно бизнес-сервис запрещает создать заказ из пустой корзины. Связи M:N реализованы через OrderItem и Favorite.

### Даталогическая модель
| Модель | Основные поля и типы Django |
| --- | --- |
| User | email: EmailField; role: CharField с choices; avatar: ImageField |
| Category | name: CharField; slug: SlugField; image: ImageField; даты: DateTimeField |
| Product | category: ForeignKey; article: CharField; price: DecimalField; stock: PositiveIntegerField; image: ImageField; specification_file: FileField |
| Favorite | user/product: ForeignKey; created_at: DateTimeField |
| CartItem | user/product: ForeignKey; quantity: PositiveIntegerField; даты: DateTimeField |
| Order | user: ForeignKey; status/payment_method: CharField с choices; total: DecimalField; даты: DateTimeField |
| OrderItem | order/product: ForeignKey; unit_price: DecimalField; quantity: PositiveIntegerField; снимки названия и артикула |
| Review | author/product: ForeignKey; rating: PositiveSmallIntegerField; text: TextField; is_approved: BooleanField |
| SiteSetting | shop_name: CharField; contact_email: EmailField; тексты: TextField |

Django создаёт первичные ключи моделей. Уникальность задаётся для email пользователя, артикула и slug товара, номера заказа, а также пар user/product в корзине и избранном, order/product в позициях заказа и author/product в отзывах.

### Реализация связей и ограничений
~~~python
category = models.ForeignKey(
    Category, on_delete=models.PROTECT,
    related_name='products', verbose_name='Серия'
)

favorited_by_users = models.ManyToManyField(
    settings.AUTH_USER_MODEL, through='Favorite',
    related_name='favorite_products', blank=True,
    verbose_name='Добавили в избранное'
)
~~~

PROTECT предотвращает удаление используемой серии. Для заказанных товаров также предусмотрена защита ссылки. Удаление корзины, избранного и отзывов следует политикам CASCADE соответствующих полей.

Временные метки предусмотрены у ключевых сущностей. История Product и Order сохраняется django-simple-history; автор записи истории заполняется при поддерживаемом сценарии запроса с HistoryRequestMiddleware. Отдельного поля редактора у каждой предметной модели нет.

### Результат и вывод
Определены девять предметных моделей и две связи M:N. Изображения и документы вынесены в файловые поля, денежные значения используют DecimalField. В предоставленном выводе showmigrations предметные миграции отмечены [X], а migrate сообщает No migrations to apply. Структура базы соответствует применённым миграциям.

### Источники
Модели users, products, cart, orders, product_reviews и siteconfig; публичные страницы LEGO и Brickset, указанные выше.
