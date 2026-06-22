import django.core.validators
from django.db import migrations, models
from django.utils import timezone


def populate_order_numbers(apps, schema_editor):
    """Заполняет номера для уже существующих заказов (на пустой БД — no-op)."""
    Order = apps.get_model('orders', 'Order')
    day = timezone.now().strftime('%Y%m%d')
    for index, order in enumerate(Order.objects.filter(order_number='').order_by('id'), start=1):
        order.order_number = f'KK-{day}-{index:04d}'
        order.save(update_fields=['order_number'])


class Migration(migrations.Migration):

    dependencies = [
        ('orders', '0002_alter_order_total'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='order',
            options={'ordering': ('-created_at',), 'verbose_name': 'заказ', 'verbose_name_plural': 'заказы'},
        ),
        migrations.RenameField('order', old_name='phone', new_name='recipient_phone'),
        migrations.RenameField('orderitem', old_name='article', new_name='product_article'),
        migrations.AlterField(
            model_name='order',
            name='recipient_phone',
            field=models.CharField(
                max_length=20,
                validators=[django.core.validators.RegexValidator(r'^\+?\d[\d\s\-()]{9,19}$', 'Укажите корректный номер телефона.')],
                verbose_name='Телефон',
            ),
        ),
        migrations.AddField(
            model_name='order',
            name='city',
            field=models.CharField(default='', max_length=100, verbose_name='Город'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='order',
            name='street',
            field=models.CharField(default='', max_length=200, verbose_name='Улица'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='order',
            name='house',
            field=models.CharField(default='', max_length=20, verbose_name='Дом'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='order',
            name='apartment',
            field=models.CharField(blank=True, max_length=20, verbose_name='Квартира'),
        ),
        migrations.AddField(
            model_name='order',
            name='postal_code',
            field=models.CharField(
                default='',
                max_length=6,
                validators=[django.core.validators.RegexValidator(r'^\d{6}$', 'Индекс должен состоять из 6 цифр.')],
                verbose_name='Индекс',
            ),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='order',
            name='comment',
            field=models.TextField(blank=True, verbose_name='Комментарий'),
        ),
        migrations.AddField(
            model_name='order',
            name='paid_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Оплачен'),
        ),
        migrations.AddField(
            model_name='order',
            name='delivered_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Доставлен'),
        ),
        migrations.AddField(
            model_name='order',
            name='cancelled_at',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Отменён'),
        ),
        migrations.AddField(
            model_name='order',
            name='order_number',
            field=models.CharField(blank=True, default='', max_length=24, verbose_name='Номер заказа'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='order',
            name='delivery_address',
            field=models.CharField(blank=True, max_length=400, verbose_name='Адрес доставки'),
        ),
        migrations.AlterField(
            model_name='order',
            name='payment_method',
            field=models.CharField(
                choices=[
                    ('cash', 'Наличными при получении'),
                    ('card_on_delivery', 'Картой при получении'),
                    ('online_mock', 'Онлайн-оплата (демо)'),
                ],
                max_length=20,
                verbose_name='Оплата',
            ),
        ),
        migrations.AlterField(
            model_name='order',
            name='total',
            field=models.DecimalField(
                decimal_places=2,
                max_digits=12,
                validators=[
                    django.core.validators.MinValueValidator(500),
                    django.core.validators.MaxValueValidator(100000),
                ],
                verbose_name='Сумма',
            ),
        ),
        migrations.AlterField(
            model_name='order',
            name='status',
            field=models.CharField(
                choices=[
                    ('new', 'Новый'),
                    ('processing', 'В обработке'),
                    ('shipped', 'Передан в доставку'),
                    ('delivered', 'Доставлен'),
                    ('cancelled', 'Отменён'),
                ],
                default='new',
                max_length=20,
                verbose_name='Статус',
            ),
        ),
        migrations.AlterField(
            model_name='order',
            name='recipient_name',
            field=models.CharField(max_length=150, verbose_name='Получатель'),
        ),
        migrations.AlterField(
            model_name='orderitem',
            name='product_article',
            field=models.CharField(max_length=40, verbose_name='Артикул'),
        ),
        migrations.AlterField(
            model_name='orderitem',
            name='product_name',
            field=models.CharField(max_length=200, verbose_name='Название'),
        ),
        migrations.AlterField(
            model_name='orderitem',
            name='unit_price',
            field=models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Цена за штуку'),
        ),
        migrations.AlterField(
            model_name='orderitem',
            name='quantity',
            field=models.PositiveIntegerField(
                validators=[django.core.validators.MinValueValidator(1)], verbose_name='Количество'
            ),
        ),
        migrations.RunPython(populate_order_numbers, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='order',
            name='order_number',
            field=models.CharField(blank=True, max_length=24, unique=True, verbose_name='Номер заказа'),
        ),
    ]
