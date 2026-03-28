from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include

from . import views

urlpatterns = [
    path('admin/', admin.site.urls),

    # API
    path('api/auth/', include('users.urls')),
    path('api/pets/', include('pets.urls')),
    path('api/doctors/', include('doctors.urls')),
    path('api/services/', include('services.urls')),
    path('api/', include('appointments.urls')),
    path('api/reviews/', include('reviews.urls')),

    # Frontend
    path('', views.IndexView.as_view(), name='index'),
    path('doctors/', views.DoctorListView.as_view(), name='doctor-list'),
    path('doctors/<int:pk>/', views.DoctorDetailView.as_view(), name='doctor-detail'),
    path('services/', views.ServiceListView.as_view(), name='service-list'),
    path('appointment/', views.AppointmentCreateView.as_view(), name='appointment-create'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('login/callback/', views.OAuthCallbackView.as_view(), name='oauth-callback'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
