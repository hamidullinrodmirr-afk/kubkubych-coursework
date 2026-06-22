import django.core.validators
import django.utils.timezone
from django.db import migrations, models
from django.utils.text import slugify


def populate_product_slugs(apps, schema_editor):
    """Заполняет slug для уже существующих наборов (на пустой БД — no-op)."""
    Product = apps.get_model('products', 'Product')
    for product in Product.objects.all():
        if not product.slug:
            base = slugify(product.name, allow_unicode=True) or 'set'
            product.slug = f'{base}-{product.article}'.lower()
            product.save(update_fields=['slug'])


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0002_alter_category_options_alter_product_options_and_more'),
    ]

    operations = [
        migrations.RenameField('product', old_name='age_min', new_name='age_from'),
        migrations.RenameField('product', old_name='age_max', new_name='age_to'),
        migrations.AlterField(
            model_name='product',
            name='age_from',
            field=models.PositiveSmallIntegerField(
                'Возраст от', validators=[django.core.validators.MinValueValidator(0)]
            ),
        ),
        migrations.AlterField(
            model_name='product',
            name='age_to',
            field=models.PositiveSmallIntegerField(
                'Возраст до', validators=[django.core.validators.MinValueValidator(0)]
            ),
        ),
        migrations.AddField(
            model_name='category',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='categories/', verbose_name='Изображение'),
        ),
        migrations.AddField(
            model_name='category',
            name='is_active',
            field=models.BooleanField(default=True, verbose_name='Активна'),
        ),
        migrations.AddField(
            model_name='category',
            name='max_discount_percent',
            field=models.PositiveSmallIntegerField(
                default=80,
                validators=[django.core.validators.MaxValueValidator(80)],
                verbose_name='Максимальная скидка серии, %',
            ),
        ),
        migrations.AddField(
            model_name='category',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='category',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='product',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='products/', verbose_name='Изображение'),
        ),
        migrations.AddField(
            model_name='product',
            name='slug',
            field=models.SlugField(blank=True, default='', max_length=220, verbose_name='Slug'),
        ),
        migrations.RunPython(populate_product_slugs, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='product',
            name='slug',
            field=models.SlugField(
                allow_unicode=True, blank=True, max_length=220, unique=True, verbose_name='Slug'
            ),
        ),
        migrations.AlterModelOptions(name='favorite', options={'ordering': ('-created_at',)}),
        migrations.AddConstraint(
            model_name='category',
            constraint=models.CheckConstraint(
                check=models.Q(max_discount_percent__gte=0) & models.Q(max_discount_percent__lte=80),
                name='category_max_discount_range',
            ),
        ),
    ]
