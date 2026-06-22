from rest_framework import serializers

from .models import Category, Product


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'description')


class ProductSerializer(serializers.ModelSerializer):
    category_detail = CategorySerializer(source='category', read_only=True)
    final_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    in_stock = serializers.SerializerMethodField()
    is_favorite = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = ('id', 'name', 'article', 'description', 'category', 'category_detail', 'age_min', 'age_max', 'pieces', 'price', 'discount_percent', 'final_price', 'stock', 'in_stock', 'image_url', 'is_active', 'is_favorite')
        read_only_fields = ('article',)

    def get_in_stock(self, obj):
        return obj.stock > 0

    def get_is_favorite(self, obj):
        request = self.context.get('request')
        return bool(request and request.user.is_authenticated and obj.favorited_by.filter(user=request.user).exists())
