from decimal import Decimal

from django.core.management.base import BaseCommand

from products.models import Category, Product
from users.models import User


class Command(BaseCommand):
    help = 'Создаёт демонстрационный каталог и аккаунты магазина КубКубыч.'

    def handle(self, *args, **options):
        category_data = {
            'city': 'LEGO City', 'technic': 'LEGO Technic', 'star-wars': 'LEGO Star Wars',
            'harry-potter': 'LEGO Harry Potter', 'creator': 'LEGO Creator 3-in-1', 'duplo': 'LEGO DUPLO',
        }
        categories = {
            slug: Category.objects.update_or_create(slug=slug, defaults={'name': name})[0]
            for slug, name in category_data.items()
        }
        data = [
            ('60420', 'Жёлтый строительный экскаватор', 'city', 8, 12, 633, '6499', 10, 7),
            ('60422', 'Приморская гавань с грузовым судном', 'city', 8, 14, 1226, '12999', 0, 5),
            ('60430', 'Межзвёздный космический корабль', 'city', 6, 12, 240, '3499', 15, 11),
            ('60316', 'Полицейский участок', 'city', 6, 12, 668, '8999', 10, 4),
            ('60337', 'Экспресс-пассажирский поезд', 'city', 7, 14, 764, '15999', 0, 3),
            ('42171', 'Mercedes-AMG F1 W14 E Performance', 'technic', 18, 99, 1642, '24999', 0, 4),
            ('42161', 'Lamborghini Huracán Tecnica', 'technic', 9, 16, 806, '8999', 12, 6),
            ('42154', 'Ford GT 2022', 'technic', 18, 99, 1466, '19999', 5, 2),
            ('42151', 'Bugatti Bolide', 'technic', 9, 16, 905, '7499', 10, 7),
            ('75375', 'Тысячелетний сокол', 'star-wars', 18, 99, 921, '12999', 15, 3),
            ('75379', 'R2-D2', 'star-wars', 10, 16, 1050, '9999', 0, 5),
            ('75355', 'X-wing Starfighter', 'star-wars', 18, 99, 1949, '22999', 0, 2),
            ('75331', 'Бритвенный гребень', 'star-wars', 18, 99, 6187, '69999', 5, 1),
            ('76435', 'Хогвартс: Большой зал', 'harry-potter', 10, 16, 1732, '16999', 0, 3),
            ('76419', 'Хогвартс: замок и территория', 'harry-potter', 18, 99, 2660, '21999', 5, 2),
            ('76415', 'Битва за Хогвартс', 'harry-potter', 9, 14, 730, '7999', 10, 6),
            ('31150', 'Дикие животные сафари', 'creator', 9, 14, 780, '6999', 0, 8),
            ('31134', 'Космический шаттл', 'creator', 9, 14, 144, '1799', 5, 12),
            ('31109', 'Пиратский корабль', 'creator', 9, 14, 1264, '11999', 15, 4),
            ('10967', 'Полицейский мотоцикл', 'duplo', 2, 4, 5, '999', 0, 15),
            ('10941', 'Микки Маус и Минни Маус', 'duplo', 2, 5, 9, '1499', 0, 14),
            ('10954', 'Поезд с цифрами', 'duplo', 2, 4, 23, '2499', 10, 15),
        ]
        for article, name, category, min_age, max_age, pieces, price, discount, stock in data:
            Product.objects.update_or_create(
                article=article,
                defaults={
                    'name': name, 'category': categories[category],
                    'description': f'Коллекционный набор «{name}»: детали для увлекательной сборки, игры и демонстрации на полке.',
                    'age_min': min_age, 'age_max': max_age, 'pieces': pieces, 'price': Decimal(price),
                    'discount_percent': discount, 'stock': stock, 'is_active': True,
                    'image_url': f'https://images.brickset.com/sets/images/{article}-1.jpg',
                },
            )
        accounts = [
            ('admin@kubkubych.ru', 'admin123', 'Радмир', 'Хамидуллин', 'admin'),
            ('buyer@kubkubych.ru', 'buyer123', 'Анна', 'Соколова', 'client'),
            ('collector@kubkubych.ru', 'collector123', 'Илья', 'Волков', 'client'),
        ]
        for email, password, first_name, last_name, role in accounts:
            user, created = User.objects.get_or_create(
                email=email,
                defaults={'first_name': first_name, 'last_name': last_name, 'role': role, 'is_staff': role == 'admin', 'is_superuser': role == 'admin'},
            )
            if created:
                user.set_password(password)
                user.save()
        self.stdout.write(self.style.SUCCESS('Создано 22 набора и 3 тестовых аккаунта.'))
        self.stdout.write('Администратор: admin@kubkubych.ru / admin123')
        self.stdout.write('Покупатель: buyer@kubkubych.ru / buyer123')
        self.stdout.write('Коллекционер: collector@kubkubych.ru / collector123')
