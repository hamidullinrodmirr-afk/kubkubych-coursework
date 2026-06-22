from django.contrib import admin

from .models import SiteSetting


@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    list_display = ('shop_name', 'contact_email', 'contact_phone', 'updated_at')
    fieldsets = (
        ('Контакты', {'fields': ('shop_name', 'contact_email', 'contact_phone', 'address')}),
        ('Тексты страниц', {'fields': ('about_text', 'mission_text', 'delivery_text')}),
    )

    def has_add_permission(self, request) -> bool:
        # Настройки магазина — единственная запись.
        return not SiteSetting.objects.exists()

    def has_delete_permission(self, request, obj=None) -> bool:
        return False
