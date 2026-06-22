from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from . import views

urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/auth/', include('users.urls')),
    path('api/products/', include('products.urls')),
    path('api/cart/', include('cart.urls')),
    path('api/orders/', include('orders.urls')),
    path('api/reviews/', include('product_reviews.urls')),

    path('', views.IndexView.as_view(), name='index'),
    path('catalog/', views.CatalogView.as_view(), name='catalog'),
    path('catalog/<int:pk>/', views.ProductDetailView.as_view(), name='product-detail'),
    path('cart/', views.CartView.as_view(), name='cart'),
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('login/callback/', views.OAuthCallbackView.as_view(), name='oauth-callback'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if getattr(settings, 'SILKY_ENABLED', False):
    urlpatterns.append(path('silk/', include('silk.urls', namespace='silk')))
