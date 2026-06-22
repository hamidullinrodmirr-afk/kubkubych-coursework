from rest_framework import serializers
from orders.models import Order
from .models import Review

class ReviewSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.full_name', read_only=True)
    class Meta:
        model = Review
        fields = ('id', 'product', 'author_name', 'rating', 'text', 'is_approved', 'created_at', 'updated_at')
        read_only_fields = ('is_approved', 'created_at', 'updated_at')
    def validate_product(self, product):
        user = self.context['request'].user
        if not Order.objects.filter(user=user, status=Order.Status.DELIVERED, items__product=product).exists():
            raise serializers.ValidationError('Отзыв можно оставить только на купленный и доставленный набор.')
        return product
    def create(self, validated_data):
        return Review.objects.create(author=self.context['request'].user, **validated_data)
