from decimal import Decimal
from django.test import TestCase
from rest_framework.test import APIClient
from users.models import User
from products.models import Category, Product
from .models import CartItem


class CartTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name='LEGO City', slug='city')
        self.product = Product.objects.create(category=category, name='Экскаватор', article='60420', description='Набор', age_min=8, age_max=12, pieces=633, price=Decimal('1000'), stock=2)
        self.user = User.objects.create_user(email='buyer@example.com', password='secret123', first_name='Иван', last_name='Иванов')
        self.client = APIClient(); self.client.force_authenticate(self.user)

    def test_cart_rejects_quantity_above_stock(self):
        response = self.client.post('/api/cart/items/', {'product': self.product.id, 'quantity': 3}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(CartItem.objects.count(), 0)

    def test_same_product_is_combined_in_cart(self):
        self.client.post('/api/cart/items/', {'product': self.product.id, 'quantity': 1}, format='json')
        response = self.client.post('/api/cart/items/', {'product': self.product.id, 'quantity': 1}, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(CartItem.objects.get().quantity, 2)
