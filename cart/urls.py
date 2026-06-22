from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CartClearView, CartItemViewSet, CartSummaryView

router = DefaultRouter()
router.register('items', CartItemViewSet, basename='cart-item')

urlpatterns = [
    path('clear/', CartClearView.as_view(), name='cart-clear'),
    path('summary/', CartSummaryView.as_view(), name='cart-summary'),
    path('', include(router.urls)),
]
