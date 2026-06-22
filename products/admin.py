from django.contrib import admin
from .models import Category, Favorite, Product

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('article', 'name', 'category', 'price', 'discount_percent', 'stock', 'is_active')
    list_filter = ('category', 'is_active')
    search_fields = ('article', 'name')

admin.site.register(Category)
admin.site.register(Favorite)
