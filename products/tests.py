from decimal import Decimal

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from rest_framework import status
from rest_framework.test import APIClient

from orders.models import Order, OrderItem
from product_reviews.models import Review
from users.models import User
from .models import Category, Favorite, Product


class ProductCatalogTests(TestCase):
    def setUp(self):
        self.category = Category.objects.create(name='LEGO City', slug='city', max_discount_percent=50)
        self.admin = User.objects.create_user(
            email='admin@kk.ru', password='adminpass123', first_name='Админ', last_name='Магазина', role='admin'
        )
        self.client_user = User.objects.create_user(
            email='client@kk.ru', password='clientpass123', first_name='Анна', last_name='Соколова'
        )
        self.product = Product.objects.create(
            category=self.category, name='Экскаватор', article='60420', description='Набор',
            age_from=8, age_to=12, pieces=633, price=Decimal('1000'), discount_percent=10, stock=5,
        )
        self.hidden = Product.objects.create(
            category=self.category, name='Скрытый', article='00000', description='Набор',
            age_from=6, age_to=10, pieces=100, price=Decimal('800'), stock=3, is_active=False,
        )

    def test_guest_sees_only_active_products(self):
        response = APIClient().get('/api/products/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        articles = {item['article'] for item in response.data['results']}
        self.assertIn('60420', articles)
        self.assertNotIn('00000', articles)

    def test_admin_sees_inactive_products(self):
        client = APIClient()
        client.force_authenticate(self.admin)
        articles = {item['article'] for item in client.get('/api/products/').data['results']}
        self.assertIn('00000', articles)

    def test_final_price_applies_discount(self):
        item = APIClient().get('/api/products/').data['results']
        target = next(p for p in item if p['article'] == '60420')
        self.assertEqual(target['final_price'], '900.00')

    def test_discount_above_limit_rejected(self):
        client = APIClient()
        client.force_authenticate(self.admin)
        payload = {
            'category': self.category.id, 'name': 'Дорогой', 'article': '99999', 'description': 'x',
            'age_from': 5, 'age_to': 10, 'pieces': 100, 'price': '1000', 'discount_percent': 90, 'stock': 1,
        }
        response = client.post('/api/products/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_discount_above_category_limit_rejected(self):
        client = APIClient()
        client.force_authenticate(self.admin)
        payload = {
            'category': self.category.id, 'name': 'Слишком', 'article': '88888', 'description': 'x',
            'age_from': 5, 'age_to': 10, 'pieces': 100, 'price': '1000', 'discount_percent': 70, 'stock': 1,
        }
        response = client.post('/api/products/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filter_by_category(self):
        other = Category.objects.create(name='Technic', slug='technic')
        Product.objects.create(
            category=other, name='Болид', article='42151', description='x',
            age_from=9, age_to=16, pieces=900, price=Decimal('7000'), stock=2,
        )
        response = APIClient().get(f'/api/products/?category={self.category.id}')
        self.assertEqual(response.data['count'], 1)

    def test_filter_by_price(self):
        Product.objects.create(
            category=self.category, name='Дешёвый', article='10001', description='x',
            age_from=4, age_to=8, pieces=50, price=Decimal('500'), stock=2,
        )
        response = APIClient().get('/api/products/?max_price=600')
        articles = {item['article'] for item in response.data['results']}
        self.assertEqual(articles, {'10001'})

    def test_annotations_present_in_response(self):
        order = Order.objects.create(
            user=self.client_user, recipient_name='Анна', recipient_phone='+79990000000',
            city='Москва', street='Л', house='1', postal_code='101000',
            payment_method=Order.PaymentMethod.CASH, status=Order.Status.DELIVERED, total=Decimal('900'),
        )
        OrderItem.objects.create(
            order=order, product=self.product, product_name=self.product.name,
            product_article=self.product.article, unit_price=Decimal('900'), quantity=2,
        )
        Review.objects.create(author=self.client_user, product=self.product, rating=4, text='Отличный набор!', is_approved=True)
        Favorite.objects.create(user=self.client_user, product=self.product)

        item = next(p for p in APIClient().get('/api/products/').data['results'] if p['article'] == '60420')
        self.assertEqual(item['average_rating'], 4.0)
        self.assertEqual(item['reviews_count'], 1)
        self.assertEqual(item['favorites_count'], 1)
        self.assertEqual(item['sold_units'], 2)

    def test_is_favorite_via_context(self):
        Favorite.objects.create(user=self.client_user, product=self.product)
        client = APIClient()
        client.force_authenticate(self.client_user)
        item = next(p for p in client.get('/api/products/').data['results'] if p['article'] == '60420')
        self.assertTrue(item['is_favorite'])

    def test_favorite_requires_authorization(self):
        response = APIClient().post(f'/api/products/{self.product.id}/favorite/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_product_list_has_no_n_plus_one(self):
        for index in range(6):
            product = Product.objects.create(
                category=self.category, name=f'Набор {index}', article=f'7{index:04d}', description='x',
                age_from=5, age_to=10, pieces=100, price=Decimal('1500'), stock=4,
            )
            Favorite.objects.create(user=self.client_user, product=product)
            Review.objects.create(author=self.client_user, product=product, rating=5, text='Понравилось всем!', is_approved=True)
        with CaptureQueriesContext(connection) as ctx:
            APIClient().get('/api/products/')
        self.assertLessEqual(len(ctx), 6)


class CategoryApiTests(TestCase):
    def test_public_categories_list_only_active(self):
        Category.objects.create(name='City', slug='city')
        Category.objects.create(name='Скрытая', slug='hidden', is_active=False)
        response = APIClient().get('/api/categories/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        slugs = {c['slug'] for c in response.data['results']}
        self.assertEqual(slugs, {'city'})
