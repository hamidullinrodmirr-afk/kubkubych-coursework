from django.urls import path

from .views import LowStockAnalyticsView, ProductsAnalyticsView, SalesAnalyticsView, UsersAnalyticsView

urlpatterns = [
    path('sales/', SalesAnalyticsView.as_view(), name='analytics-sales'),
    path('products/', ProductsAnalyticsView.as_view(), name='analytics-products'),
    path('users/', UsersAnalyticsView.as_view(), name='analytics-users'),
    path('low-stock/', LowStockAnalyticsView.as_view(), name='analytics-low-stock'),
]
