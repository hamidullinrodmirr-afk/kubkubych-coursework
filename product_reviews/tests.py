from decimal import Decimal

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from orders.models import Order, OrderItem
from products.models import Category, Product
from users.models import User
from .models import Review

REVIEW_TEXT = 'Отличный набор, собирали всей семьёй и остались довольны.'


class ReviewTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name='LEGO City', slug='city')
        self.product = Product.objects.create(
            category=category, name='Экскаватор', article='60420', description='Набор',
            age_from=8, age_to=12, pieces=633, price=Decimal('1000'), stock=5,
        )
        self.buyer = User.objects.create_user(email='buyer@example.com', password='secret123', first_name='И', last_name='И')
        self.admin = User.objects.create_user(email='admin@example.com', password='secret123', first_name='А', last_name='А', role='admin')
        self.client = APIClient()
        self.client.force_authenticate(self.buyer)

    def _deliver(self, user=None, status_value=Order.Status.DELIVERED):
        order = Order.objects.create(
            user=user or self.buyer, recipient_name='И', recipient_phone='+79990000000',
            city='Москва', street='Л', house='1', postal_code='101000',
            payment_method=Order.PaymentMethod.CASH, status=status_value, total=Decimal('1000'),
        )
        OrderItem.objects.create(
            order=order, product=self.product, product_name=self.product.name,
            product_article=self.product.article, unit_price=Decimal('1000'), quantity=1,
        )

    def test_review_requires_purchase(self):
        response = self.client.post('/api/reviews/', {'product': self.product.id, 'rating': 5, 'text': REVIEW_TEXT}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_review_requires_delivered_status(self):
        self._deliver(status_value=Order.Status.PROCESSING)
        response = self.client.post('/api/reviews/', {'product': self.product.id, 'rating': 5, 'text': REVIEW_TEXT}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_review_allowed_after_delivery(self):
        self._deliver()
        response = self.client.post('/api/reviews/', {'product': self.product.id, 'rating': 5, 'text': REVIEW_TEXT}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_second_review_rejected(self):
        self._deliver()
        self.client.post('/api/reviews/', {'product': self.product.id, 'rating': 5, 'text': REVIEW_TEXT}, format='json')
        response = self.client.post('/api/reviews/', {'product': self.product.id, 'rating': 4, 'text': REVIEW_TEXT}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_public_list_shows_only_approved(self):
        Review.objects.create(author=self.buyer, product=self.product, rating=5, text=REVIEW_TEXT, is_approved=True)
        other = User.objects.create_user(email='c@example.com', password='secret123', first_name='К', last_name='К')
        Review.objects.create(author=other, product=self.product, rating=2, text=REVIEW_TEXT, is_approved=False)
        response = APIClient().get('/api/reviews/')
        self.assertEqual(response.data['count'], 1)

    def test_admin_can_moderate_review(self):
        review = Review.objects.create(author=self.buyer, product=self.product, rating=5, text=REVIEW_TEXT, is_approved=False)
        client = APIClient()
        client.force_authenticate(self.admin)
        response = client.patch(f'/api/reviews/{review.id}/moderate/', {'is_approved': True}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        review.refresh_from_db()
        self.assertTrue(review.is_approved)

    def test_edit_sends_review_back_to_moderation(self):
        review = Review.objects.create(author=self.buyer, product=self.product, rating=5, text=REVIEW_TEXT, is_approved=True)
        response = self.client.patch(f'/api/reviews/{review.id}/', {'text': 'Обновлённый отзыв про набор'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        review.refresh_from_db()
        self.assertFalse(review.is_approved)
