from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

class Review(models.Model):
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='product_reviews')
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='reviews')
    rating = models.PositiveSmallIntegerField(validators=(MinValueValidator(1), MaxValueValidator(5)))
    text = models.TextField()
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ('-created_at',)
        constraints = [models.UniqueConstraint(fields=('author', 'product'), name='unique_product_review')]
