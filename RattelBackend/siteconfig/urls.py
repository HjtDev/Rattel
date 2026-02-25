from django.urls import path
from . import views


app_name = 'siteconfig'

urlpatterns = [
    path('footer/', views.FooterView.as_view(), name='footer'),
    path('navbar/', views.NavbarView.as_view(), name='navbar'),
    path('mainpage/', views.MainPageView.as_view(), name='mainpage'),
]
