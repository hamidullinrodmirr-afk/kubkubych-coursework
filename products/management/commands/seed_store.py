from decimal import Decimal
from django.core.management.base import BaseCommand
from products.models import Category, Product
from users.models import User


class Command(BaseCommand):
    help = 'Создаёт демонстрационные данные магазина КубКубыч.'
    def handle(self, *args, **options):
        categories = {
            'city': 'LEGO City', 'technic': 'LEGO Technic', 'star-wars': 'LEGO Star Wars',
            'harry-potter': 'LEGO Harry Potter', 'creator': 'LEGO Creator', 'duplo': 'LEGO Duplo',
        }
        categories = {slug: Category.objects.get_or_create(slug=slug, defaults={'name': name})[0] for slug, name in categories.items()}
        data = [
            ('60420', 'Жёлтый строительный экскаватор', 'city', 8, 12, 633, '6499', 10, 7),
            ('42171', 'Mercedes-AMG F1 W14 E Performance', 'technic', 18, 99, 1642, '24999', 0, 4),
            ('75375', 'Тысячелетний сокол', 'star-wars', 18, 99, 921, '12999', 15, 3),
            ('76419', 'Хогвартс: замок и территория', 'harry-potter', 18, 99, 2660, '21999', 0, 2),
            ('31134', 'Космический шаттл', 'creator', 9, 14, 144, '1799', 5, 12),
            ('10954', 'Поезд с цифрами', 'duplo', 2, 4, 23, '2499', 0, 15),
        ]
        for article, name, category, min_age, max_age, pieces, price, discount, stock in data:
            Product.objects.update_or_create(article=article, defaults={'name': name, 'category': categories[category], 'description': f'Оригинальный набор {name} для творчества и коллекции.', 'age_min': min_age, 'age_max': max_age, 'pieces': pieces, 'price': Decimal(price), 'discount_percent': discount, 'stock': stock, 'is_active': True})
        admin, created = User.objects.get_or_create(email='admin@kubkubych.ru', defaults={'first_name': 'Радмир', 'last_name': 'Хамидуллин', 'role': 'admin', 'is_staff': True, 'is_superuser': True})
        if created:
            admin.set_password('admin123'); admin.save()
        self.stdout.write(self.style.SUCCESS('Демо-данные КубКубыча созданы. Администратор: admin@kubkubych.ru / admin123'))
