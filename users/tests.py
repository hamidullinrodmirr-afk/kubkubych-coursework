from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient

User = get_user_model()


class RegistrationTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_register_success(self):
        data = {
            'email': 'test@example.com', 'first_name': 'Иван', 'last_name': 'Петров',
            'phone': '+79991234567', 'password': 'securepass123', 'password_confirm': 'securepass123',
        }
        response = self.client.post('/api/auth/register/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['role'], 'client')
        self.assertTrue(User.objects.filter(email='test@example.com').exists())

    def test_register_duplicate_email_rejected(self):
        User.objects.create_user(email='dup@example.com', password='securepass123', first_name='А', last_name='Б')
        data = {
            'email': 'dup@example.com', 'first_name': 'Иван', 'last_name': 'Петров',
            'password': 'securepass123', 'password_confirm': 'securepass123',
        }
        response = self.client.post('/api/auth/register/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_password_mismatch(self):
        data = {
            'email': 'm@example.com', 'first_name': 'Иван', 'last_name': 'Петров',
            'password': 'securepass123', 'password_confirm': 'wrongpassword',
        }
        response = self.client.post('/api/auth/register/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_weak_password_rejected(self):
        data = {
            'email': 'weak@example.com', 'first_name': 'Иван', 'last_name': 'Петров',
            'password': '12345678', 'password_confirm': '12345678',
        }
        response = self.client.post('/api/auth/register/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(email='weak@example.com').exists())


class AuthenticationTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='auth@example.com', password='testpass123', first_name='Тест', last_name='Юзер'
        )

    def test_login_success(self):
        response = self.client.post('/api/auth/login/', {'email': 'auth@example.com', 'password': 'testpass123'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_login_wrong_password(self):
        response = self.client.post('/api/auth/login/', {'email': 'auth@example.com', 'password': 'wrong'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_blocked_user_cannot_login(self):
        self.user.is_active = False
        self.user.save(update_fields=('is_active',))
        response = self.client.post('/api/auth/login/', {'email': 'auth@example.com', 'password': 'testpass123'})
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_refresh(self):
        login = self.client.post('/api/auth/login/', {'email': 'auth@example.com', 'password': 'testpass123'})
        response = self.client.post('/api/auth/refresh/', {'refresh': login.data['refresh']})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)


class UserModerationTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_user(
            email='admin@example.com', password='adminpass123', first_name='Админ', last_name='Магазина', role='admin'
        )
        self.buyer = User.objects.create_user(
            email='buyer@example.com', password='buyerpass123', first_name='Покупатель', last_name='Тестовый'
        )

    def test_client_cannot_list_users(self):
        self.client.force_authenticate(self.buyer)
        self.assertEqual(self.client.get('/api/users/').status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_list_users(self):
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.get('/api/users/').status_code, status.HTTP_200_OK)

    def test_admin_can_block_buyer(self):
        self.client.force_authenticate(self.admin)
        response = self.client.patch(f'/api/users/{self.buyer.id}/block/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.buyer.refresh_from_db()
        self.assertFalse(self.buyer.is_active)

    def test_admin_can_change_role(self):
        self.client.force_authenticate(self.admin)
        response = self.client.patch(f'/api/users/{self.buyer.id}/role/', {'role': 'admin'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.buyer.refresh_from_db()
        self.assertTrue(self.buyer.is_admin_role())
