from decimal import Decimal
from django.test import TestCase
from rest_framework.test import APIClient
from users.models import User
from .models import Category, Product


class ProductApiTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='LEGO City', slug='city')
        self.product = Product.objects.create(category=self.category, name='Экскаватор', article='60420', description='Набор', age_min=8, age_max=12, pieces=633, price=Decimal('1000'), discount_percent=10, stock=3)

    def test_public_catalog_shows_active_products_and_final_price(self):
        response = APIClient().get('/api/products/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['results'][0]['final_price'], '900.00')

    def test_favorite_requires_authorization(self):
        response = APIClient().post(f'/api/products/{self.product.id}/favorite/')
        self.assertEqual(response.status_code, 401)
