from django.contrib import admin

from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('author', 'product', 'rating', 'is_approved', 'created_at')
    list_filter = ('rating', 'is_approved', 'created_at')
    search_fields = ('author__email', 'product__name', 'text')
    actions = ('approve_selected', 'unapprove_selected')

    @admin.action(description='Одобрить выбранные отзывы')
    def approve_selected(self, request, queryset):
        queryset.update(is_approved=True)

    @admin.action(description='Снять одобрение')
    def unapprove_selected(self, request, queryset):
        queryset.update(is_approved=False)
