from django.contrib import admin

from .models import Category, Favorite, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'max_discount_percent')
    list_filter = ('is_active',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'article', 'category', 'price', 'discount_percent', 'final_price', 'stock', 'is_active')
    list_filter = ('category', 'is_active', 'discount_percent')
    search_fields = ('name', 'article')
    prepopulated_fields = {'slug': ('name',)}

    @admin.display(description='Цена со скидкой')
    def final_price(self, obj: Product):
        return obj.final_price


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'created_at')
    search_fields = ('user__email', 'product__name')
