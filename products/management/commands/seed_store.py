from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from orders.models import Order, OrderItem
from product_reviews.models import Review
from products.models import Category, Favorite, Product
from siteconfig.models import SiteSetting
from users.models import User

# slug, название, максимальная скидка серии
CATEGORIES = [
    ('city', 'LEGO City', 50),
    ('technic', 'LEGO Technic', 40),
    ('star-wars', 'LEGO Star Wars', 30),
    ('icons', 'LEGO Icons', 25),
    ('creator', 'LEGO Creator 3-in-1', 60),
    ('ninjago', 'LEGO Ninjago', 50),
    ('friends', 'LEGO Friends', 55),
    ('minecraft', 'LEGO Minecraft', 50),
]

# артикул, название, серия, возраст от, возраст до, деталей, цена, скидка %, остаток
PRODUCTS = [
    ('60420', 'Жёлтый строительный экскаватор', 'city', 8, 12, 633, '6499', 10, 7),
    ('60316', 'Полицейский участок', 'city', 6, 12, 668, '8999', 10, 4),
    ('60337', 'Экспресс-пассажирский поезд', 'city', 7, 14, 764, '15999', 0, 0),
    ('42171', 'Mercedes-AMG F1 W14 E Performance', 'technic', 18, 99, 1642, '24999', 0, 4),
    ('42161', 'Lamborghini Huracán Tecnica', 'technic', 9, 16, 806, '8999', 12, 6),
    ('42154', 'Ford GT 2022', 'technic', 18, 99, 1466, '19999', 5, 2),
    ('42151', 'Bugatti Bolide', 'technic', 9, 16, 905, '7499', 10, 0),
    ('75375', 'Тысячелетний сокол', 'star-wars', 18, 99, 921, '12999', 15, 3),
    ('75379', 'R2-D2', 'star-wars', 10, 16, 1050, '9999', 0, 5),
    ('75355', 'X-wing Starfighter', 'star-wars', 18, 99, 1949, '22999', 0, 2),
    ('10330', 'McLaren MP4/4 и Айртон Сенна', 'icons', 18, 99, 693, '8999', 5, 4),
    ('10311', 'Орхидея', 'icons', 18, 99, 608, '4999', 0, 9),
    ('10302', 'Optimus Prime', 'icons', 18, 99, 1508, '14999', 10, 3),
    ('31150', 'Дикие животные сафари', 'creator', 9, 14, 780, '6999', 0, 8),
    ('31134', 'Космический шаттл', 'creator', 9, 14, 144, '1799', 20, 12),
    ('31109', 'Пиратский корабль', 'creator', 9, 14, 1264, '11999', 15, 4),
    ('71795', 'Храмовый додзё ниндзя', 'ninjago', 9, 14, 648, '7499', 5, 6),
    ('71799', 'Ниндзяго-Сити: рынок', 'ninjago', 10, 16, 6163, '32999', 0, 1),
    ('71789', 'Кай и Рас: бой машин', 'ninjago', 7, 12, 103, '999', 0, 15),
    ('42634', 'Конюшня с лошадьми и пони', 'friends', 4, 8, 42, '1299', 0, 14),
    ('41732', 'Центр цветов и дизайна', 'friends', 8, 13, 808, '7999', 10, 5),
    ('41744', 'Спортивный центр', 'friends', 6, 11, 832, '6499', 0, 0),
    ('21241', 'Деревня в биоме берёзового леса', 'minecraft', 8, 13, 1276, '10999', 5, 4),
    ('21261', 'Побег на лодке', 'minecraft', 8, 12, 524, '4499', 0, 10),
]

REVIEWS = [
    ('60420', 5, 'Экскаватор собрали за вечер, кабина крутится, ковш реально копает. Сын в восторге.', True),
    ('42161', 4, 'Модель детализированная, но наклейки клеить тяжеловато. В целом доволен покупкой.', True),
    ('75379', 5, 'R2-D2 получился как настоящий, голова поворачивается. Отличный подарок фанату.', True),
    ('31134', 3, 'Маленький, но из него три модели. За свою цену нормально, ждали побольше.', False),
    ('10311', 5, 'Орхидея стоит на столе вместо живого цветка, выглядит дорого и аккуратно.', True),
]

FAVORITES = ['75375', '42171', '10302', '71799']

SITE_TEXTS = {
    'about_text': (
        'КубКубыч — интернет-магазин конструкторов LEGO. Мы собираем каталог из проверенных '
        'наборов популярных серий и помогаем выбрать подходящий по возрасту, бюджету и интересам.'
    ),
    'mission_text': (
        'Наша миссия — дарить радость совместной сборки. Конструктор объединяет за столом детей и '
        'взрослых, развивает внимание и воображение, превращает вечер в маленькое приключение.'
    ),
    'delivery_text': (
        'Доставляем по всей России: курьером по Москве за 1–2 дня и почтой в регионы за 3–7 дней. '
        'Оплата картой онлайн, картой или наличными при получении. Минимальная сумма заказа — 500 ₽.'
    ),
}


class Command(BaseCommand):
    help = 'Наполняет магазин КубКубыч демонстрационными данными (идемпотентно).'

    @transaction.atomic
    def handle(self, *args, **options):
        categories = {
            slug: Category.objects.update_or_create(
                slug=slug, defaults={'name': name, 'max_discount_percent': max_discount, 'is_active': True}
            )[0]
            for slug, name, max_discount in CATEGORIES
        }

        products = {}
        for article, name, slug, age_from, age_to, pieces, price, discount, stock in PRODUCTS:
            product, _ = Product.objects.update_or_create(
                article=article,
                defaults={
                    'name': name,
                    'category': categories[slug],
                    'description': (
                        f'Конструктор «{name}» серии {categories[slug].name}: {pieces} деталей '
                        'для увлекательной сборки, игры и эффектной демонстрации на полке.'
                    ),
                    'age_from': age_from,
                    'age_to': age_to,
                    'pieces': pieces,
                    'price': Decimal(price),
                    'discount_percent': discount,
                    'stock': stock,
                    'is_active': True,
                    'image_url': f'https://images.brickset.com/sets/images/{article}-1.jpg',
                },
            )
            products[article] = product

        accounts = [
            ('admin@kubkubych.ru', 'admin123', 'Радмир', 'Хамидуллин', User.Role.ADMIN),
            ('buyer@kubkubych.ru', 'buyer123', 'Анна', 'Соколова', User.Role.CLIENT),
            ('collector@kubkubych.ru', 'collector123', 'Илья', 'Волков', User.Role.CLIENT),
        ]
        users = {}
        for email, password, first_name, last_name, role in accounts:
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'first_name': first_name,
                    'last_name': last_name,
                    'role': role,
                    'is_staff': role == User.Role.ADMIN,
                    'is_superuser': role == User.Role.ADMIN,
                },
            )
            if created:
                user.set_password(password)
                user.save()
            users[email] = user

        buyer = users['buyer@kubkubych.ru']
        self._seed_delivered_order(buyer, [('60420', 1), ('42161', 1), ('75379', 1)])
        self._seed_delivered_order(users['collector@kubkubych.ru'], [('10311', 2)])

        for article, rating, text, approved in REVIEWS:
            Review.objects.get_or_create(
                author=buyer,
                product=products[article],
                defaults={'rating': rating, 'text': text, 'is_approved': approved},
            )

        for article in FAVORITES:
            Favorite.objects.get_or_create(user=buyer, product=products[article])

        settings_obj = SiteSetting.load()
        for field, value in SITE_TEXTS.items():
            setattr(settings_obj, field, value)
        settings_obj.save()

        self.stdout.write(self.style.SUCCESS(
            f'Готово: {len(categories)} серий, {len(products)} наборов, '
            f'{Order.objects.count()} заказов, {Review.objects.count()} отзывов.'
        ))
        self.stdout.write('Администратор: admin@kubkubych.ru / admin123')
        self.stdout.write('Покупатель: buyer@kubkubych.ru / buyer123')

    def _seed_delivered_order(self, user, lines: list[tuple[str, int]]) -> None:
        """Создаёт доставленный заказ, если у пользователя ещё нет заказов."""
        if Order.objects.filter(user=user).exists():
            return
        items = [(Product.objects.get(article=article), quantity) for article, quantity in lines]
        total = sum((product.final_price * quantity for product, quantity in items), Decimal('0.00'))
        order = Order.objects.create(
            user=user,
            recipient_name=user.full_name,
            recipient_phone='+79991234567',
            city='Москва',
            street='Тверская',
            house='7',
            postal_code='101000',
            payment_method=Order.PaymentMethod.CARD_ON_DELIVERY,
            status=Order.Status.DELIVERED,
            total=total,
            delivered_at=timezone.now(),
        )
        for product, quantity in items:
            OrderItem.objects.create(
                order=order,
                product=product,
                product_name=product.name,
                product_article=product.article,
                unit_price=product.final_price,
                quantity=quantity,
            )
