from decimal import Decimal

from django.core import mail
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from cart.models import CartItem
from products.models import Category, Product
from users.models import User
from .models import Order

VALID_CHECKOUT = {
    'recipient_name': 'Иван Иванов', 'recipient_phone': '+79990000000',
    'city': 'Москва', 'street': 'Тверская', 'house': '7', 'postal_code': '101000',
    'payment_method': 'card_on_delivery',
}


class OrderCheckoutTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name='LEGO City', slug='city')
        self.product = Product.objects.create(
            category=category, name='Экскаватор', article='60420', description='Набор',
            age_from=8, age_to=12, pieces=633, price=Decimal('1000'), stock=5,
        )
        self.cheap = Product.objects.create(
            category=category, name='Брелок', article='30000', description='Мелочь',
            age_from=4, age_to=8, pieces=20, price=Decimal('100'), stock=5,
        )
        self.user = User.objects.create_user(
            email='buyer@example.com', password='secret123', first_name='Иван', last_name='Иванов'
        )
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def _add(self, product, quantity):
        CartItem.objects.create(user=self.user, product=product, quantity=quantity)

    def test_empty_cart_rejected(self):
        response = self.client.post('/api/orders/', VALID_CHECKOUT, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_order_below_minimum_rejected(self):
        self._add(self.cheap, 1)
        response = self.client.post('/api/orders/', VALID_CHECKOUT, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_address_rejected(self):
        self._add(self.product, 1)
        payload = {**VALID_CHECKOUT, 'postal_code': '12', 'city': ''}
        response = self.client.post('/api/orders/', payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_checkout_decreases_stock_and_clears_cart(self):
        self._add(self.product, 2)
        response = self.client.post('/api/orders/', VALID_CHECKOUT, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 3)
        self.assertEqual(CartItem.objects.filter(user=self.user).count(), 0)

    def test_order_item_stores_snapshot(self):
        self._add(self.product, 1)
        created = self.client.post('/api/orders/', VALID_CHECKOUT, format='json')
        item = Order.objects.get(id=created.data['id']).items.first()
        self.assertEqual(item.product_name, self.product.name)
        self.assertEqual(item.product_article, self.product.article)
        self.assertEqual(item.unit_price, self.product.final_price)

    def test_confirmation_email_sent_on_checkout(self):
        self._add(self.product, 1)
        with self.captureOnCommitCallbacks(execute=True):
            response = self.client.post('/api/orders/', VALID_CHECKOUT, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(self.user.email, mail.outbox[0].to)


class OrderAccessTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name='LEGO City', slug='city')
        self.product = Product.objects.create(
            category=category, name='Экскаватор', article='60420', description='Набор',
            age_from=8, age_to=12, pieces=633, price=Decimal('1000'), stock=5,
        )
        self.buyer = User.objects.create_user(email='buyer@example.com', password='secret123', first_name='И', last_name='И')
        self.other = User.objects.create_user(email='other@example.com', password='secret123', first_name='П', last_name='П')
        self.admin = User.objects.create_user(email='admin@example.com', password='secret123', first_name='А', last_name='А', role='admin')
        self.order = Order.objects.create(
            user=self.buyer, recipient_name='И', recipient_phone='+79990000000',
            city='Москва', street='Л', house='1', postal_code='101000',
            payment_method=Order.PaymentMethod.CASH, status=Order.Status.NEW, total=Decimal('1000'),
        )

    def test_buyer_sees_only_own_orders(self):
        Order.objects.create(
            user=self.other, recipient_name='П', recipient_phone='+79990000001',
            city='Москва', street='Л', house='2', postal_code='101000',
            payment_method=Order.PaymentMethod.CASH, status=Order.Status.NEW, total=Decimal('1000'),
        )
        client = APIClient()
        client.force_authenticate(self.buyer)
        self.assertEqual(client.get('/api/orders/').data['count'], 1)

    def test_buyer_cannot_open_foreign_order(self):
        client = APIClient()
        client.force_authenticate(self.other)
        self.assertEqual(client.get(f'/api/orders/{self.order.id}/').status_code, status.HTTP_404_NOT_FOUND)

    def test_admin_can_change_status(self):
        client = APIClient()
        client.force_authenticate(self.admin)
        response = client.patch(f'/api/orders/{self.order.id}/status/', {'status': 'processing'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, Order.Status.PROCESSING)

    def test_invalid_status_transition_rejected(self):
        client = APIClient()
        client.force_authenticate(self.admin)
        response = client.patch(f'/api/orders/{self.order.id}/status/', {'status': 'delivered'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_client_cannot_change_status(self):
        client = APIClient()
        client.force_authenticate(self.buyer)
        response = client.patch(f'/api/orders/{self.order.id}/status/', {'status': 'processing'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
