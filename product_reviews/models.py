from django.conf import settings
from django.core.validators import MaxValueValidator, MinLengthValidator, MinValueValidator
from django.db import models

REVIEW_MIN_TEXT_LENGTH = 10


class Review(models.Model):
    """Отзыв покупателя о наборе с модерацией администратором."""

    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='product_reviews')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField('Оценка', validators=(MinValueValidator(1), MaxValueValidator(5)))
    text = models.TextField('Текст', validators=[MinLengthValidator(REVIEW_MIN_TEXT_LENGTH)])
    is_approved = models.BooleanField('Одобрен', default=False)
    moderation_comment = models.TextField('Комментарий модератора', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created_at',)
        verbose_name = 'отзыв'
        verbose_name_plural = 'отзывы'
        constraints = [models.UniqueConstraint(fields=('author', 'product'), name='unique_product_review')]

    def __str__(self) -> str:
        return f'{self.author} → {self.product} ({self.rating}★)'
