from django.urls import path

from . import views

urlpatterns = [
    path('', views.UserListView.as_view(), name='user-list'),
    path('<int:pk>/', views.UserDetailView.as_view(), name='user-detail'),
    path('<int:pk>/role/', views.UserRoleView.as_view(), name='user-role'),
    path('<int:pk>/block/', views.UserBlockView.as_view(), name='user-block'),
    path('<int:pk>/unblock/', views.UserUnblockView.as_view(), name='user-unblock'),
]
