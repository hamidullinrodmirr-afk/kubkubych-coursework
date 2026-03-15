from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email обязателен')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', User.Role.ADMIN)
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
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

    def __str__(self):
        return f'{self.last_name} {self.first_name} ({self.get_role_display()})'

    @property
    def full_name(self):
        return f'{self.last_name} {self.first_name}'.strip()
