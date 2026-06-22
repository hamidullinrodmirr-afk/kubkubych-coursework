from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from orders.models import Order, OrderItem
from products.models import Category, Product
from users.models import User


class ReviewTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name='LEGO City', slug='city')
        self.product = Product.objects.create(
            category=category, name='Экскаватор', article='60420', description='Набор',
            age_from=8, age_to=12, pieces=633, price=Decimal('1000'), stock=2,
        )
        self.user = User.objects.create_user(
            email='buyer@example.com', password='secret123', first_name='Иван', last_name='Иванов'
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def _deliver_product(self):
        order = Order.objects.create(
            user=self.user, recipient_name='Иван', recipient_phone='+79990000000',
            city='Москва', street='Ленина', house='1', postal_code='101000',
            payment_method=Order.PaymentMethod.CASH, status=Order.Status.DELIVERED, total=Decimal('1000'),
        )
        OrderItem.objects.create(
            order=order, product=self.product, product_name=self.product.name,
            product_article=self.product.article, unit_price=Decimal('1000'), quantity=1,
        )

    def test_review_is_available_only_after_delivered_order(self):
        payload = {'product': self.product.id, 'rating': 5, 'text': 'Отличный набор для сборки'}
        response = self.client.post('/api/reviews/', payload, format='json')
        self.assertEqual(response.status_code, 400)

        self._deliver_product()
        response = self.client.post('/api/reviews/', payload, format='json')
        self.assertEqual(response.status_code, 201)
