from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL), ('products', '0001_initial')]
    operations = [
        migrations.CreateModel(name='Order', fields=[('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')), ('recipient_name', models.CharField(max_length=150)), ('phone', models.CharField(max_length=30)), ('delivery_address', models.TextField()), ('payment_method', models.CharField(choices=[('card', 'Банковская карта'), ('cash', 'При получении')], max_length=20)), ('status', models.CharField(choices=[('new', 'Новый'), ('processing', 'В обработке'), ('shipped', 'Передан в доставку'), ('delivered', 'Доставлен'), ('cancelled', 'Отменён')], default='new', max_length=20)), ('total', models.DecimalField(decimal_places=2, max_digits=12)), ('created_at', models.DateTimeField(auto_now_add=True)), ('updated_at', models.DateTimeField(auto_now=True)), ('user', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='orders', to=settings.AUTH_USER_MODEL))], options={'ordering': ('-created_at',)}),
        migrations.CreateModel(name='OrderItem', fields=[('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')), ('product_name', models.CharField(max_length=200)), ('article', models.CharField(max_length=40)), ('unit_price', models.DecimalField(decimal_places=2, max_digits=10)), ('quantity', models.PositiveIntegerField()), ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='orders.order')), ('product', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='order_items', to='products.product'))]),
        migrations.AddConstraint(model_name='orderitem', constraint=models.UniqueConstraint(fields=('order', 'product'), name='unique_order_product')),
    ]
