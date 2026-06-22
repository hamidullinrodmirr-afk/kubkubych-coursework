from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

from users.models import User


class HealthCheckTest(TestCase):
    def test_health_endpoint_is_public(self):
        response = APIClient().get('/api/health/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'ok')


class AnalyticsAccessTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            email='admin@kk.ru', password='adminpass123', first_name='А', last_name='А', role='admin'
        )
        self.client_user = User.objects.create_user(
            email='client@kk.ru', password='clientpass123', first_name='К', last_name='К'
        )

    def test_analytics_requires_admin(self):
        client = APIClient()
        client.force_authenticate(self.client_user)
        for endpoint in ('sales', 'products', 'users', 'low-stock'):
            self.assertEqual(client.get(f'/api/analytics/{endpoint}/').status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_open_analytics(self):
        client = APIClient()
        client.force_authenticate(self.admin)
        for endpoint in ('sales', 'products', 'users', 'low-stock'):
            self.assertEqual(client.get(f'/api/analytics/{endpoint}/').status_code, status.HTTP_200_OK)
