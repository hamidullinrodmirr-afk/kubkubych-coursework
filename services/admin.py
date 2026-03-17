from django.contrib import admin
from .models import Service


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('name', 'specialty', 'price', 'duration_minutes', 'is_active')
    list_filter = ('is_active', 'specialty')
    search_fields = ('name',)
