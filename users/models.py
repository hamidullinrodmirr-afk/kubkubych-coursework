from typing import Any

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    """Менеджер пользователей с email вместо username."""

    def create_user(self, email: str, password: str | None = None, **extra_fields: Any) -> 'User':
        """Создаёт пользователя с нормализованным email и хешированным паролем.

        Args:
            email: Адрес электронной почты (обязателен).
            password: Пароль в открытом виде; None — неиспользуемый пароль.
            **extra_fields: Дополнительные поля модели.

        Returns:
            Созданный пользователь.

        Raises:
            ValueError: Если email не указан.
        """
        if not email:
            raise ValueError('Email обязателен')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str | None = None, **extra_fields: Any) -> 'User':
        """Создаёт суперпользователя с ролью администратора.

        Args:
            email: Адрес электронной почты.
            password: Пароль в открытом виде.
            **extra_fields: Дополнительные поля модели.

        Returns:
            Созданный суперпользователь.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', User.Role.ADMIN)
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Пользователь системы с ролью: клиент, ветеринар или администратор."""

    class Role(models.TextChoices):
        CLIENT = 'client', 'Клиент'
        VETERINARIAN = 'veterinarian', 'Ветеринар'
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
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self) -> str:
        return f'{self.last_name} {self.first_name} ({self.get_role_display()})'

    @property
    def full_name(self) -> str:
        """Фамилия и имя одной строкой."""
        return f'{self.last_name} {self.first_name}'.strip()
