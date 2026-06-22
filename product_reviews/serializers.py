from rest_framework import serializers

from orders.models import Order
from .models import Review


class ReviewSerializer(serializers.ModelSerializer):
    """Чтение и редактирование отзыва автором."""

    author_name = serializers.CharField(source='author.full_name', read_only=True)

    class Meta:
        model = Review
        fields = (
            'id', 'product', 'author_name', 'rating', 'text',
            'is_approved', 'moderation_comment', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'product', 'is_approved', 'moderation_comment', 'created_at', 'updated_at')


class ReviewCreateSerializer(serializers.ModelSerializer):
    """Создание отзыва: только на купленный и доставленный набор."""

    class Meta:
        model = Review
        fields = ('id', 'product', 'rating', 'text')

    def validate_product(self, product):
        user = self.context['request'].user
        delivered = Order.objects.filter(
            user=user, status=Order.Status.DELIVERED, items__product=product
        ).exists()
        if not delivered:
            raise serializers.ValidationError('Отзыв можно оставить только на купленный и доставленный набор.')
        if Review.objects.filter(author=user, product=product).exists():
            raise serializers.ValidationError('Вы уже оставляли отзыв на этот набор.')
        return product

    def create(self, validated_data: dict) -> Review:
        return Review.objects.create(author=self.context['request'].user, **validated_data)


class ReviewModerationSerializer(serializers.ModelSerializer):
    """Модерация отзыва администратором."""

    class Meta:
        model = Review
        fields = ('id', 'is_approved', 'moderation_comment')
        read_only_fields = ('id',)
