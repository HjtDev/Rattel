from django.urls import path
from . import views


app_name = 'authentication'

urlpatterns = [
    path('login/', views.LoginView.as_view(), name='JWT-login'),
    path('register/', views.RegisterView.as_view(), name='JWT-register'),
    path('verify/', views.VerifyView.as_view(), name='JWT-verify'),
    path('refresh/', views.RefreshView.as_view(), name='JWT-refresh'),
]