from decimal import Decimal

from rest_framework import serializers

from .constants import MAX_DISCOUNT_PERCENT
from .models import Category, Favorite, Product


class CategorySerializer(serializers.ModelSerializer):
    """Серия конструкторов для каталога и админ-управления."""

    class Meta:
        model = Category
        fields = ('id', 'name', 'slug', 'description', 'image', 'is_active', 'max_discount_percent')
        read_only_fields = ('id',)


class ProductListSerializer(serializers.ModelSerializer):
    """Карточка набора для списка: вычисляемые поля и агрегаты из аннотаций."""

    category_detail = CategorySerializer(source='category', read_only=True)
    final_price = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    discount_amount = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    in_stock = serializers.BooleanField(read_only=True)
    average_rating = serializers.SerializerMethodField()
    reviews_count = serializers.SerializerMethodField()
    sold_units = serializers.SerializerMethodField()
    favorites_count = serializers.SerializerMethodField()
    is_favorite = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = (
            'id', 'name', 'slug', 'article', 'category', 'category_detail',
            'age_from', 'age_to', 'pieces', 'price', 'discount_percent',
            'final_price', 'discount_amount', 'stock', 'in_stock',
            'image', 'image_url', 'is_active',
            'average_rating', 'reviews_count', 'sold_units', 'favorites_count', 'is_favorite',
        )

    def get_average_rating(self, obj: Product) -> float:
        value = getattr(obj, 'average_rating', None)
        return round(float(value), 2) if value is not None else 0.0

    def get_reviews_count(self, obj: Product) -> int:
        return int(getattr(obj, 'reviews_count', 0) or 0)

    def get_sold_units(self, obj: Product) -> int:
        return int(getattr(obj, 'sold_units', 0) or 0)

    def get_favorites_count(self, obj: Product) -> int:
        return int(getattr(obj, 'favorites_count', 0) or 0)

    def get_is_favorite(self, obj: Product) -> bool:
        """Признак избранного без N+1: id читается из набора в context."""
        return obj.id in self.context.get('favorite_product_ids', set())


class ProductDetailSerializer(ProductListSerializer):
    """Карточка набора с описанием и одобренными отзывами."""

    reviews = serializers.SerializerMethodField()

    class Meta(ProductListSerializer.Meta):
        fields = ProductListSerializer.Meta.fields + ('description', 'created_at', 'updated_at', 'reviews')

    def get_reviews(self, obj: Product) -> list[dict]:
        reviews = getattr(obj, 'approved_reviews', None)
        if reviews is None:
            reviews = obj.reviews.filter(is_approved=True).select_related('author')
        return [
            {
                'id': review.id,
                'author': review.author.full_name,
                'rating': review.rating,
                'text': review.text,
                'created_at': review.created_at,
            }
            for review in reviews
        ]


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    """Создание и редактирование набора администратором с бизнес-валидацией."""

    class Meta:
        model = Product
        fields = (
            'id', 'category', 'name', 'slug', 'article', 'description',
            'age_from', 'age_to', 'pieces', 'price', 'discount_percent',
            'stock', 'image', 'image_url', 'is_active',
        )
        read_only_fields = ('id', 'slug')

    def validate(self, attrs: dict) -> dict:
        """Повторяет ограничения модели на уровне API (цена, скидка, возраст)."""
        instance = self.instance
        category = attrs.get('category') or (instance.category if instance else None)
        price = attrs.get('price', instance.price if instance else None)
        discount = attrs.get('discount_percent', instance.discount_percent if instance else 0)
        age_from = attrs.get('age_from', instance.age_from if instance else None)
        age_to = attrs.get('age_to', instance.age_to if instance else None)

        errors: dict[str, str] = {}
        if price is not None and price <= 0:
            errors['price'] = 'Цена должна быть больше нуля.'
        if age_from is not None and age_to is not None and age_to < age_from:
            errors['age_to'] = 'Возраст «до» не может быть меньше возраста «от».'
        if discount > MAX_DISCOUNT_PERCENT:
            errors['discount_percent'] = f'Скидка не может превышать {MAX_DISCOUNT_PERCENT}%.'
        if category is not None and discount > category.max_discount_percent:
            errors['discount_percent'] = (
                f'Скидка превышает лимит серии «{category.name}» ({category.max_discount_percent}%).'
            )
        if price is not None:
            final_price = price * (Decimal('100') - discount) / Decimal('100')
            if final_price <= 0:
                errors['discount_percent'] = 'Итоговая цена со скидкой должна быть больше нуля.'
        if errors:
            raise serializers.ValidationError(errors)
        return attrs


class FavoriteSerializer(serializers.ModelSerializer):
    """Запись избранного с краткой карточкой набора."""

    product_detail = ProductListSerializer(source='product', read_only=True)

    class Meta:
        model = Favorite
        fields = ('id', 'product', 'product_detail', 'created_at')
        read_only_fields = ('id', 'created_at')
