from decimal import Decimal
from django.test import TestCase
from rest_framework.test import APIClient
from users.models import User
from products.models import Category, Product
from cart.models import CartItem
from .models import Order


class OrderTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name='LEGO City', slug='city')
        self.product = Product.objects.create(category=category, name='Экскаватор', article='60420', description='Набор', age_min=8, age_max=12, pieces=633, price=Decimal('1000'), stock=2)
        self.user = User.objects.create_user(email='buyer@example.com', password='secret123', first_name='Иван', last_name='Иванов')
        CartItem.objects.create(user=self.user, product=self.product, quantity=1)
        self.client = APIClient(); self.client.force_authenticate(self.user)

    def test_checkout_creates_snapshot_and_decreases_stock(self):
        response = self.client.post('/api/orders/', {'recipient_name': 'Иван Иванов', 'phone': '+79990000000', 'delivery_address': 'Москва, Ленина, 1, 101000', 'payment_method': 'card'}, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Order.objects.count(), 1)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 1)
        self.assertEqual(CartItem.objects.count(), 0)

    def test_checkout_rejects_invalid_address(self):
        response = self.client.post('/api/orders/', {'recipient_name': 'Иван', 'phone': '+7999', 'delivery_address': 'Москва', 'payment_method': 'card'}, format='json')
        self.assertEqual(response.status_code, 400)
