from django.urls import path

from .views import SiteSettingView

urlpatterns = [
    path('', SiteSettingView.as_view(), name='site-settings'),
]
