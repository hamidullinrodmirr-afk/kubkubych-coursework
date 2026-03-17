from django.contrib import admin
from .models import Review


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('author', 'doctor', 'rating', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'rating')
    search_fields = ('text', 'author__last_name', 'doctor__user__last_name')
    raw_id_fields = ('author', 'doctor', 'appointment')
    actions = ['approve_reviews']

    @admin.action(description='Одобрить выбранные отзывы')
    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)
