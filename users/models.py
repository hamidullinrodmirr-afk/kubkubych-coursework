from django.contrib.auth.models import AbstractUser
from django.db import models

from .managers import UserManager


class User(AbstractUser):
    """Пользователь интернет-магазина: покупатель или администратор."""

    class Role(models.TextChoices):
        CLIENT = 'client', 'Покупатель'
        ADMIN = 'admin', 'Администратор'

    username = None
    email = models.EmailField('Email', unique=True)
    phone = models.CharField('Телефон', max_length=20, blank=True)
    role = models.CharField('Роль', max_length=20, choices=Role.choices, default=Role.CLIENT)
    avatar = models.ImageField('Аватар', upload_to='avatars/', blank=True, null=True)
    updated_at = models.DateTimeField('Обновлён', auto_now=True)

    objects = UserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        verbose_name = 'пользователь'
        verbose_name_plural = 'пользователи'

    @property
    def full_name(self) -> str:
        return f'{self.last_name} {self.first_name}'.strip()

    def is_admin_role(self) -> bool:
        return self.role == self.Role.ADMIN

    def is_client_role(self) -> bool:
        return self.role == self.Role.CLIENT

    def __str__(self) -> str:
        return f'{self.full_name} ({self.get_role_display()})'
