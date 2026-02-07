from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("create/", views.create, name="create"),
    path("ticket/<int:pk>/", views.ticket_detail, name="ticket_detail"),
    path("ticket/<int:pk>/rate/", views.rate_ticket, name="rate_ticket"),
    path("create-admin/", views.create_admin, name="create_admin"),
    path("seed-demo/", views.seed_demo_view, name="seed_demo"),
    path("admin-queue/", views.admin_queue, name="admin_queue"),
    path("admin-queue/<int:pk>/status/", views.admin_ticket_status, name="admin_ticket_status"),
    path("signup/", views.signup, name="signup"),
    path("account/", views.account, name="account"),
    path("account/avatar/", views.upload_avatar, name="upload_avatar"),

    # REST API
    path("api/tickets/", views.TicketListCreateAPI.as_view(), name="api_tickets"),
    path("api/tickets/<int:pk>/", views.TicketDetailAPI.as_view(), name="api_ticket_detail"),
    path("api/ai/generate/", views.ai_generate, name="api_ai_generate"),
]
