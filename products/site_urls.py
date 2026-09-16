from django.urls import path

from . import site_views


urlpatterns = [
    path('', site_views.product_manage_list, name='product-manage-list'),
    path('create/', site_views.product_create, name='product-manage-create'),
    path('<int:pk>/edit/', site_views.product_update, name='product-manage-update'),
    path('<int:pk>/delete/', site_views.product_delete, name='product-manage-delete'),
]
