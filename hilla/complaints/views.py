from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages

from .models import Ticket, Category
from .forms import TicketForm

# DRF
from rest_framework import generics
from .serializers import TicketSerializer


def index(request):
    tickets = Ticket.objects.select_related("category").all()
    stats = {
        "total": Ticket.objects.count(),
        "open": Ticket.objects.filter(status=Ticket.OPEN).count(),
        "in_progress": Ticket.objects.filter(status=Ticket.IN_PROGRESS).count(),
        "closed": Ticket.objects.filter(status=Ticket.CLOSED).count(),
    }
    recent = Ticket.objects.select_related("category").order_by("-created_at")[:3]
    return render(
        request,
        "complaints/index.html",
        {"tickets": tickets, "stats": stats, "recent": recent},
    )


def create(request):
    if request.method == "POST":
        form = TicketForm(request.POST)
        if form.is_valid():
            ticket = form.save(commit=False)
            if request.user.is_authenticated:
                ticket.user = request.user
            ticket.save()
            messages.success(request, "Ticket created successfully!")
            return redirect("ticket_detail", pk=ticket.pk)
    else:
        form = TicketForm()

    return render(request, "complaints/support_form.html", {"form": form})


def ticket_detail(request, pk: int):
    ticket = get_object_or_404(Ticket.objects.select_related("category"), pk=pk)
    comments = ticket.comments.all()
    return render(
        request,
        "complaints/ticket_detail.html",
        {"ticket": ticket, "comments": comments},
    )


# ==========================
# REST API (для Postman/curl)
# ==========================

class TicketListCreateAPI(generics.ListCreateAPIView):
    queryset = Ticket.objects.all().order_by("-created_at")
    serializer_class = TicketSerializer


class TicketDetailAPI(generics.RetrieveUpdateDestroyAPIView):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer
