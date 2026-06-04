from django.urls import path
from .views import PlanListView, MySubscriptionView

app_name = 'subscriptions'

urlpatterns = [
    path('plans/', PlanListView.as_view(), name='plan-list'),
    path('my/', MySubscriptionView.as_view(), name='my-subscription'),
]
