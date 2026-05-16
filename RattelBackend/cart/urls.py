from django.urls import path
from . import views


app_name = 'cart'

urlpatterns = [
    path('', views.CartView.as_view(), name='cart'),
    path('length/', views.CartLengthView.as_view(), name='cart-length'),
    path('total-price/', views.CartTotalPriceView.as_view(), name='cart-total-price'),
    path('finalize/', views.CartFinalizerView.as_view(), name='cart-finalize'),
]
