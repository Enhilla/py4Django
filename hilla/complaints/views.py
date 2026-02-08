import json
import os

from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Avg
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect, get_object_or_404
from django.core.management import call_command

from .models import Ticket, Category
from .forms import TicketForm, TicketRatingForm, AdminCreateForm

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
            if ticket.is_anonymous:
                ticket.name = ""
                ticket.email = ""
            ticket.save()
            messages.success(request, "Ticket created successfully!")
            return redirect("ticket_detail", pk=ticket.pk)
    else:
        form = TicketForm()

    return render(request, "complaints/support_form.html", {"form": form})


def ticket_detail(request, pk: int):
    ticket = get_object_or_404(Ticket.objects.select_related("category"), pk=pk)
    rating_form = TicketRatingForm()
    ratings = ticket.ratings.all()
    avg_rating = ratings.aggregate(avg=Avg("score"))["avg"]
    comments = ticket.comments.all()
    return render(
        request,
        "complaints/ticket_detail.html",
        {
            "ticket": ticket,
            "comments": comments,
            "ratings": ratings,
            "avg_rating": avg_rating,
            "rating_form": rating_form,
        },
    )


def rate_ticket(request, pk: int):
    ticket = get_object_or_404(Ticket, pk=pk)
    if request.method != "POST":
        return redirect("ticket_detail", pk=pk)
    form = TicketRatingForm(request.POST)
    if form.is_valid():
        rating = form.save(commit=False)
        rating.ticket = ticket
        rating.save()
        messages.success(request, "Thanks for your rating!")
    else:
        messages.error(request, "Please fix the rating form.")
    return redirect("ticket_detail", pk=pk)


def dashboard(request):
    status_counts = (
        Ticket.objects.values("status")
        .annotate(count=Count("id"))
        .order_by()
    )
    priority_counts = (
        Ticket.objects.values("priority")
        .annotate(count=Count("id"))
        .order_by()
    )
    category_counts = (
        Category.objects.annotate(count=Count("tickets"))
        .values("name", "count")
        .order_by("-count")[:5]
    )
    avg_rating = Ticket.objects.aggregate(avg=Avg("ratings__score"))["avg"]

    leaderboard = (
        Ticket.objects.filter(is_anonymous=False)
        .values("name")
        .annotate(total=Count("id"), avg=Avg("ratings__score"))
        .order_by("-total")[:5]
    )

    return render(
        request,
        "complaints/dashboard.html",
        {
            "status_counts": status_counts,
            "priority_counts": priority_counts,
            "category_counts": category_counts,
            "avg_rating": avg_rating,
            "leaderboard": leaderboard,
        },
    )


@login_required
@user_passes_test(lambda u: u.is_superuser)
def create_admin(request):
    if request.method == "POST":
        form = AdminCreateForm(request.POST)
        if form.is_valid():
            User = get_user_model()
            user = User.objects.create_user(
                username=form.cleaned_data["username"],
                email=form.cleaned_data.get("email", ""),
                password=form.cleaned_data["password1"],
            )
            user.is_staff = True
            user.is_superuser = True
            user.save()
            messages.success(request, "Admin created.")
            return redirect("create_admin")
    else:
        form = AdminCreateForm()
    return render(request, "complaints/create_admin.html", {"form": form})


@login_required
@user_passes_test(lambda u: u.is_superuser)
def seed_demo_view(request):
    if request.method == "POST":
        count = int(request.POST.get("count", "8") or "8")
        call_command("seed_demo", count=count)
        messages.success(request, f"Seeded {count} demo tickets.")
        return redirect("seed_demo")
    return render(request, "complaints/seed_demo.html")


def signup(request):
    if request.user.is_authenticated:
        return redirect("index")
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created.")
            return redirect("index")
    else:
        form = UserCreationForm()
    return render(request, "registration/signup.html", {"form": form})


# ==========================
# REST API (для Postman/curl)
# ==========================

class TicketListCreateAPI(generics.ListCreateAPIView):
    queryset = Ticket.objects.all().order_by("-created_at")
    serializer_class = TicketSerializer


class TicketDetailAPI(generics.RetrieveUpdateDestroyAPIView):
    queryset = Ticket.objects.all()
    serializer_class = TicketSerializer


@csrf_exempt
def ai_generate(request):
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    text = (payload.get("text") or "").strip()
    mode = (payload.get("mode") or "summary").strip().lower()

    if not text:
        return JsonResponse({"error": "Empty text"}, status=400)

    if mode == "summary":
        prompt = (
            "Summarize the issue in 3 bullets: What, Where, Impact.\n\n"
            f"{text}"
        )
    elif mode == "rewrite":
        prompt = (
            "Rewrite this into a clear request for campus support, include location, "
            "impact, urgency, and desired fix. Keep it under 120 words.\n\n"
            f"{text}"
        )
    else:
        return JsonResponse({"error": "Unknown mode"}, status=400)

    provider = os.environ.get("AI_PROVIDER", "").strip().lower()
    has_openai = bool(os.environ.get("OPENAI_API_KEY"))
    has_gemini = bool(os.environ.get("GEMINI_API_KEY"))

    if not provider:
        provider = "openai" if has_openai else "gemini" if has_gemini else ""

    try:
        if provider == "gemini":
            if not has_gemini:
                return JsonResponse(
                    {"error": "GEMINI_API_KEY is not configured", "user_message": "AI ключ не настроен."},
                    status=503,
                )
            from google import genai
            client = genai.Client()
            response = client.models.generate_content(
                model=os.environ.get("GEMINI_MODEL", "gemini-2.5-flash"),
                contents=prompt,
            )
            return JsonResponse({"text": (response.text or "").strip()})

        if provider == "openai":
            if not has_openai:
                return JsonResponse(
                    {"error": "OPENAI_API_KEY is not configured", "user_message": "AI ключ не настроен."},
                    status=503,
                )
            from openai import OpenAI
            client = OpenAI()
            response = client.responses.create(
                model=os.environ.get("OPENAI_MODEL", "gpt-5-mini"),
                input=prompt,
                max_output_tokens=180,
            )
            return JsonResponse({"text": response.output_text.strip()})

        return JsonResponse(
            {"error": "No AI provider configured", "user_message": "AI провайдер не настроен."},
            status=503,
        )
    except Exception as exc:
        raw = str(exc)
        lower = raw.lower()
        user_message = "Ошибка AI. Попробуй позже."
        if "insufficient_quota" in lower or "quota" in lower:
            user_message = "Лимит запросов исчерпан. Попробуй позже."
        elif "api key" in lower or "permission" in lower or "unauthorized" in lower:
            user_message = "Неверный ключ API."
        elif "rate" in lower and "limit" in lower:
            user_message = "Слишком много запросов. Подожди немного."
        return JsonResponse({"error": raw, "user_message": user_message}, status=500)
