from django.urls import path
from . import views


app_name = 'tickets'

urlpatterns = [
    path('', views.TicketListCreateView.as_view(), name='ticket-list-create'),
    path('<uuid:ticket_id>/', views.TicketDetailView.as_view(), name='ticket-detail'),
    path('<uuid:ticket_id>/close/', views.TicketCloseView.as_view(), name='ticket-close'),
    path('<uuid:ticket_id>/reopen/', views.TicketReopenView.as_view(), name='ticket-reopen'),
    path('<uuid:ticket_id>/messages/', views.TicketMessageCreateView.as_view(), name='ticket-message-create'),
]
