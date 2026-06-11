from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

User = get_user_model()


class RegistrationTest(TestCase):
    """Тест 1: Регистрация пользователя"""

    def setUp(self):
        self.client = APIClient()

    def test_register_success(self):
        data = {
            'email': 'test@example.com',
            'first_name': 'Иван',
            'last_name': 'Петров',
            'phone': '+79991234567',
            'password': 'securepass123',
            'password_confirm': 'securepass123',
        }
        response = self.client.post('/api/auth/register/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['email'], 'test@example.com')
        self.assertEqual(response.data['role'], 'client')
        self.assertTrue(User.objects.filter(email='test@example.com').exists())

    def test_register_password_mismatch(self):
        data = {
            'email': 'test@example.com',
            'first_name': 'Иван',
            'last_name': 'Петров',
            'password': 'securepass123',
            'password_confirm': 'wrongpassword',
        }
        response = self.client.post('/api/auth/register/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_weak_password_rejected(self):
        data = {
            'email': 'weak@example.com',
            'first_name': 'Иван',
            'last_name': 'Петров',
            'password': '12345678',
            'password_confirm': '12345678',
        }
        response = self.client.post('/api/auth/register/', data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)
        self.assertFalse(User.objects.filter(email='weak@example.com').exists())


class AuthenticationTest(TestCase):
    """Тест 2: Авторизация и получение JWT токена"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='auth@example.com',
            password='testpass123',
            first_name='Тест',
            last_name='Юзер',
        )

    def test_login_success(self):
        response = self.client.post('/api/auth/login/', {
            'email': 'auth@example.com',
            'password': 'testpass123',
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_login_wrong_password(self):
        response = self.client.post('/api/auth/login/', {
            'email': 'auth@example.com',
            'password': 'wrongpassword',
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_refresh(self):
        login = self.client.post('/api/auth/login/', {
            'email': 'auth@example.com',
            'password': 'testpass123',
        })
        refresh_token = login.data['refresh']
        response = self.client.post('/api/auth/refresh/', {
            'refresh': refresh_token,
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
