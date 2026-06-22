from django.db import models


class SiteSetting(models.Model):
    """Единственная запись с контактами и текстами магазина."""

    shop_name = models.CharField('Название магазина', max_length=120, default='КубКубыч')
    contact_email = models.EmailField('Контактный email', default='hello@kubkubych.ru')
    contact_phone = models.CharField('Контактный телефон', max_length=30, default='+7 (495) 123-45-67')
    address = models.CharField('Адрес', max_length=255, default='Москва, доставка по России')
    about_text = models.TextField('О магазине', blank=True)
    mission_text = models.TextField('Миссия', blank=True)
    delivery_text = models.TextField('Доставка и оплата', blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'настройки магазина'
        verbose_name_plural = 'настройки магазина'

    def __str__(self) -> str:
        return self.shop_name

    def save(self, *args, **kwargs) -> None:
        """Singleton: всегда единственная запись с pk=1."""
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls) -> 'SiteSetting':
        """Возвращает настройки магазина, создавая запись при первом обращении."""
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj
