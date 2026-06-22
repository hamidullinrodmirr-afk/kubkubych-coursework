from decimal import Decimal
from django.test import TestCase
from rest_framework.test import APIClient
from users.models import User
from products.models import Category, Product
from orders.models import Order, OrderItem


class ReviewTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name='LEGO City', slug='city')
        self.product = Product.objects.create(category=category, name='Экскаватор', article='60420', description='Набор', age_min=8, age_max=12, pieces=633, price=Decimal('1000'), stock=2)
        self.user = User.objects.create_user(email='buyer@example.com', password='secret123', first_name='Иван', last_name='Иванов')
        self.client = APIClient(); self.client.force_authenticate(self.user)

    def test_review_is_available_only_after_delivered_order(self):
        response = self.client.post('/api/reviews/', {'product': self.product.id, 'rating': 5, 'text': 'Отличный набор'}, format='json')
        self.assertEqual(response.status_code, 400)
        order = Order.objects.create(user=self.user, recipient_name='Иван', phone='+7999', delivery_address='Москва, Ленина, 1, 101000', payment_method='card', status=Order.Status.DELIVERED, total=Decimal('1000'))
        OrderItem.objects.create(order=order, product=self.product, product_name=self.product.name, article=self.product.article, unit_price=Decimal('1000'), quantity=1)
        response = self.client.post('/api/reviews/', {'product': self.product.id, 'rating': 5, 'text': 'Отличный набор'}, format='json')
        self.assertEqual(response.status_code, 201)
