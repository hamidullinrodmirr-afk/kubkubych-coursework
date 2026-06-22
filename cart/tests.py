from decimal import Decimal

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from products.models import Category, Product
from users.models import User
from .models import CartItem


class CartTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name='LEGO City', slug='city')
        self.product = Product.objects.create(
            category=category, name='Экскаватор', article='60420', description='Набор',
            age_from=8, age_to=12, pieces=633, price=Decimal('1000'), stock=2,
        )
        self.inactive = Product.objects.create(
            category=category, name='Скрытый', article='00000', description='Набор',
            age_from=6, age_to=10, pieces=100, price=Decimal('800'), stock=5, is_active=False,
        )
        self.user = User.objects.create_user(
            email='buyer@example.com', password='secret123', first_name='Иван', last_name='Иванов'
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_add_product_to_cart(self):
        response = self.client.post('/api/cart/items/', {'product': self.product.id, 'quantity': 1}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CartItem.objects.count(), 1)

    def test_cart_rejects_quantity_above_stock(self):
        response = self.client.post('/api/cart/items/', {'product': self.product.id, 'quantity': 3}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(CartItem.objects.count(), 0)

    def test_same_product_is_combined_in_cart(self):
        self.client.post('/api/cart/items/', {'product': self.product.id, 'quantity': 1}, format='json')
        response = self.client.post('/api/cart/items/', {'product': self.product.id, 'quantity': 1}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(CartItem.objects.get().quantity, 2)

    def test_inactive_product_cannot_be_added(self):
        response = self.client.post('/api/cart/items/', {'product': self.inactive.id, 'quantity': 1}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_remove_cart_item(self):
        created = self.client.post('/api/cart/items/', {'product': self.product.id, 'quantity': 1}, format='json')
        response = self.client.delete(f"/api/cart/items/{created.data['id']}/")
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(CartItem.objects.count(), 0)

    def test_cannot_modify_foreign_cart_item(self):
        other = User.objects.create_user(email='other@example.com', password='secret123', first_name='Пётр', last_name='Петров')
        item = CartItem.objects.create(user=other, product=self.product, quantity=1)
        response = self.client.patch(f'/api/cart/items/{item.id}/', {'quantity': 2}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_clear_cart(self):
        self.client.post('/api/cart/items/', {'product': self.product.id, 'quantity': 1}, format='json')
        response = self.client.delete('/api/cart/clear/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(CartItem.objects.count(), 0)

    def test_cart_summary(self):
        self.client.post('/api/cart/items/', {'product': self.product.id, 'quantity': 2}, format='json')
        response = self.client.get('/api/cart/summary/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_quantity'], 2)
        self.assertEqual(response.data['total'], '2000.00')
