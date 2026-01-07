from django.urls import path
from . import views


app_name = 'siteconfig'

urlpatterns = [
    path('footer/', views.FooterView.as_view(), name='footer')
]
