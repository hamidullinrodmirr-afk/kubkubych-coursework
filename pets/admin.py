from django.contrib import admin
from .models import Pet


@admin.register(Pet)
class PetAdmin(admin.ModelAdmin):
    list_display = ('name', 'species', 'breed', 'owner', 'age', 'weight')
    list_filter = ('species',)
    search_fields = ('name', 'breed', 'owner__last_name', 'owner__email')
    raw_id_fields = ('owner',)
