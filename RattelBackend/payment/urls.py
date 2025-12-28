from django.urls import path
from . import views


app_name = 'payment'

urlpatterns = [
    path('start/', views.PaymentStartView.as_view(), name='start-payment'),
    path('callback/', views.PaymentCallbackView.as_view(), name='payment-callback'),
    path('finalize/', views.FinalView.as_view(), name='payment-finalize'),
]
