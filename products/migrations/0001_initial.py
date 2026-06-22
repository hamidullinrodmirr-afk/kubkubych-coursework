from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(name='Category', fields=[('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')), ('name', models.CharField(max_length=100, unique=True, verbose_name='Серия LEGO')), ('slug', models.SlugField(unique=True)), ('description', models.TextField(blank=True, verbose_name='Описание'))], options={'ordering': ('name',)}),
        migrations.CreateModel(name='Product', fields=[('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')), ('name', models.CharField(max_length=200, verbose_name='Название')), ('article', models.CharField(max_length=40, unique=True, verbose_name='Артикул')), ('description', models.TextField(verbose_name='Описание')), ('age_min', models.PositiveSmallIntegerField(verbose_name='Возраст от')), ('age_max', models.PositiveSmallIntegerField(verbose_name='Возраст до')), ('pieces', models.PositiveIntegerField(verbose_name='Количество деталей')), ('price', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Цена')), ('discount_percent', models.PositiveSmallIntegerField(default=0, verbose_name='Скидка, %')), ('stock', models.PositiveIntegerField(default=0, verbose_name='Остаток на складе')), ('image_url', models.URLField(blank=True, verbose_name='Ссылка на изображение')), ('is_active', models.BooleanField(default=True, verbose_name='Показывать в каталоге')), ('created_at', models.DateTimeField(auto_now_add=True)), ('updated_at', models.DateTimeField(auto_now=True)), ('category', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='products', to='products.category', verbose_name='Серия'))], options={'ordering': ('name',)}),
        migrations.CreateModel(name='Favorite', fields=[('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')), ('created_at', models.DateTimeField(auto_now_add=True)), ('product', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='favorited_by', to='products.product')), ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='favorites', to=settings.AUTH_USER_MODEL))]),
        migrations.AddConstraint(model_name='favorite', constraint=models.UniqueConstraint(fields=('user', 'product'), name='unique_user_favorite')),
    ]
