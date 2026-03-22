from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register('appointments', views.AppointmentViewSet, basename='appointment')
router.register('medical-records', views.MedicalRecordViewSet, basename='medical-record')

urlpatterns = [
    path('', include(router.urls)),
]
