from django.urls import path

from . import views

app_name = 'in_person_class'

urlpatterns = [
    path('', views.InPersonClassListView.as_view(), name='class-list'),
    path('categories/', views.CategoryListView.as_view(), name='category-list'),
    path('register/', views.RegisterView.as_view(), name='register'),
    path('my-registrations/', views.MyRegistrationsView.as_view(), name='my-registrations'),
]
