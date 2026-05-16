from django.urls import path
from . import views


app_name = 'users'

urlpatterns = [
    path('profile/', views.UserProfileView.as_view(), name='profile'),
    path('settings/', views.UserSettingsView.as_view(), name='settings'),
    path('info/', views.UserInfoView.as_view(), name='info'),
    path('dashboard/', views.UserDashboardView.as_view(), name='dashboard'),
]
