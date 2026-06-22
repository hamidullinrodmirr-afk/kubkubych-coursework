from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import views
from .oauth import GoogleCallbackView, GoogleLoginView, VKCallbackView, VKLoginView

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('me/', views.ProfileView.as_view(), name='profile'),

    path('oauth/google/', GoogleLoginView.as_view(), name='oauth-google'),
    path('oauth/google/callback/', GoogleCallbackView.as_view(), name='oauth-google-callback'),
    path('oauth/vk/', VKLoginView.as_view(), name='oauth-vk'),
    path('oauth/vk/callback/', VKCallbackView.as_view(), name='oauth-vk-callback'),
]
