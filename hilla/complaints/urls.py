from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("create/", views.create, name="create"),
    path("ticket/<int:pk>/", views.ticket_detail, name="ticket_detail"),

    # REST API
    path("api/tickets/", views.TicketListCreateAPI.as_view(), name="api_tickets"),
    path("api/tickets/<int:pk>/", views.TicketDetailAPI.as_view(), name="api_ticket_detail"),
]
