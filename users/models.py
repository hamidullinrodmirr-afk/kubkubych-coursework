from typing import Any

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email: str, password: str | None = None, **extra_fields: Any) -> 'User':
        if not email:
            raise ValueError('Email обязателен')
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str | None = None, **extra_fields: Any) -> 'User':
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', User.Role.ADMIN)
        return self.create_user(email, password, **extra_fields)


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

    objects = UserManager()
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    class Meta:
        verbose_name = 'пользователь'
        verbose_name_plural = 'пользователи'

    @property
    def full_name(self) -> str:
        return f'{self.last_name} {self.first_name}'.strip()

    def __str__(self) -> str:
        return f'{self.full_name} ({self.get_role_display()})'
