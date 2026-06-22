from rest_framework import serializers

from .models import SiteSetting


class SiteSettingSerializer(serializers.ModelSerializer):
    """Контакты и тексты магазина."""

    class Meta:
        model = SiteSetting
        fields = (
            'shop_name', 'contact_email', 'contact_phone', 'address',
            'about_text', 'mission_text', 'delivery_text', 'updated_at',
        )
        read_only_fields = ('updated_at',)
