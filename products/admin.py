from django.contrib import admin
from django.http import HttpResponse
from import_export.admin import ImportExportModelAdmin
from import_export import resources
from reportlab.pdfgen import canvas

from .models import Category, Favorite, Product


@admin.register(Category)
class CategoryAdmin(ImportExportModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'max_discount_percent')
    list_filter = ('is_active',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


class ProductResource(resources.ModelResource):
    class Meta:
        model = Product
        fields = ('id', 'article', 'name', 'category__name', 'price', 'stock', 'is_active')

@admin.register(Product)
class ProductAdmin(ImportExportModelAdmin):
    resource_classes = (ProductResource,)
    list_display = ('name', 'article', 'category', 'price', 'discount_percent', 'final_price', 'stock', 'is_active')
    list_filter = ('category', 'is_active', 'discount_percent')
    search_fields = ('name', 'article')
    prepopulated_fields = {'slug': ('name',)}
    date_hierarchy = 'created_at'
    list_display_links = ('name',)
    raw_id_fields = ('category',)
    readonly_fields = ('created_at', 'updated_at')
    actions = ('export_specs_pdf',)

    @admin.display(description='Цена со скидкой')
    def final_price(self, obj: Product):
        return obj.final_price

    @admin.action(description='Сформировать PDF со спецификациями выбранных наборов')
    def export_specs_pdf(self, request, queryset):
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="product-specifications.pdf"'
        pdf = canvas.Canvas(response)
        y = 800
        pdf.setTitle('Product specifications')
        for product in queryset.order_by('name'):
            pdf.drawString(40, y, f'{product.article}: {product.name}; stock={product.stock}; price={product.price}')
            y -= 24
            if y < 60:
                pdf.showPage()
                y = 800
        pdf.save()
        return response


@admin.register(Favorite)
class FavoriteAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'created_at')
    search_fields = ('user__email', 'product__name')
