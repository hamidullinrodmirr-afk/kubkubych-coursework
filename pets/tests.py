from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from .models import Pet

User = get_user_model()


class PetCRUDTest(TestCase):
    """Тест 10: CRUD питомцев"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='petowner@example.com',
            password='testpass123',
            first_name='Анна',
            last_name='Сидорова',
        )
        self.client.force_authenticate(user=self.user)

    def test_create_pet(self):
        data = {
            'name': 'Барсик',
            'species': 'cat',
            'breed': 'Британская',
            'age': 36,
            'weight': '5.50',
            'health_notes': 'Аллергия на курицу',
        }
        response = self.client.post('/api/pets/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['name'], 'Барсик')
        self.assertEqual(response.data['species_display'], 'Кошка')

    def test_list_pets(self):
        Pet.objects.create(
            owner=self.user, name='Шарик', species='dog',
            breed='Лабрадор', age=24, weight=30,
        )
        response = self.client.get('/api/pets/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)

    def test_update_pet(self):
        pet = Pet.objects.create(
            owner=self.user, name='Шарик', species='dog',
            breed='Лабрадор', age=24, weight=30,
        )
        response = self.client.patch(f'/api/pets/{pet.id}/', {'name': 'Бобик'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'Бобик')

    def test_delete_pet(self):
        pet = Pet.objects.create(
            owner=self.user, name='Шарик', species='dog',
            breed='Лабрадор', age=24, weight=30,
        )
        response = self.client.delete(f'/api/pets/{pet.id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Pet.objects.filter(id=pet.id).exists())

    def test_cannot_see_other_user_pets(self):
        other_user = User.objects.create_user(
            email='other@example.com', password='pass123',
            first_name='Другой', last_name='Юзер',
        )
        Pet.objects.create(
            owner=other_user, name='Чужой кот', species='cat',
            breed='Сиамская', age=12, weight=4,
        )
        response = self.client.get('/api/pets/')
        self.assertEqual(len(response.data['results']), 0)
