import json
import os

from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Avg, Q
from django.db.models.functions import Coalesce
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect, get_object_or_404
from django.core.management import call_command

from .models import Ticket, Category
from .forms import TicketForm, TicketRatingForm, AdminCreateForm, AvatarForm, SignUpForm
from users.models import Profile

# DRF
from rest_framework import generics
from .serializers import TicketSerializer


def _is_staff_user(user):
    return user.is_staff or user.is_superuser


def index(request):
    status = (request.GET.get("status") or "").strip().lower()
    priority = (request.GET.get("priority") or "").strip().lower()
    category = (request.GET.get("category") or "").strip().lower()
    sort = (request.GET.get("sort") or "newest").strip().lower()

    tickets = Ticket.objects.select_related("category").annotate(
        avg_rating=Coalesce(Avg("ratings__score"), 0.0)
    )

    if status in {Ticket.OPEN, Ticket.IN_PROGRESS, Ticket.CLOSED}:
        tickets = tickets.filter(status=status)
    if priority in {Ticket.LOW, Ticket.MEDIUM, Ticket.HIGH}:
        tickets = tickets.filter(priority=priority)
    if category:
        tickets = tickets.filter(category__slug=category)

    if sort == "oldest":
        tickets = tickets.order_by("created_at")
    elif sort == "rating_desc":
        tickets = tickets.order_by("-avg_rating", "-created_at")
    elif sort == "rating_asc":
        tickets = tickets.order_by("avg_rating", "-created_at")
    else:
        sort = "newest"
        tickets = tickets.order_by("-created_at")

    categories = Category.objects.order_by("name")

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
        {
            "tickets": tickets,
            "stats": stats,
            "recent": recent,
            "categories": categories,
            "filters": {
                "status": status,
                "priority": priority,
                "category": category,
                "sort": sort,
            },
        },
    )


@login_required
def create(request):
    if request.method == "POST":
        form = TicketForm(request.POST, user=request.user)
        if form.is_valid():
            ticket = form.save(commit=False)
            if request.user.is_authenticated:
                ticket.user = request.user
                if not ticket.name:
                    ticket.name = request.user.get_full_name() or request.user.username
                if not ticket.email:
                    ticket.email = request.user.email or ""
            if ticket.is_anonymous:
                ticket.name = ""
                ticket.email = ""
            ticket.save()
            messages.success(request, "Ticket created successfully!")
            return redirect("ticket_detail", pk=ticket.pk)
        first_error = ""
        if form.errors:
            errors = form.non_field_errors() or []
            if not errors:
                first_field = next(iter(form.errors))
                errors = form.errors.get(first_field) or []
            if errors:
                first_error = str(errors[0])
        messages.error(
            request,
            f"Ticket was not sent. {first_error}" if first_error else "Ticket was not sent. Please fix the form errors.",
        )
    else:
        form = TicketForm(user=request.user)

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


@login_required
@user_passes_test(_is_staff_user)
def admin_queue(request):
    status = (request.GET.get("status") or "").strip().lower()
    priority = (request.GET.get("priority") or "").strip().lower()
    category = (request.GET.get("category") or "").strip().lower()
    sort = (request.GET.get("sort") or "newest").strip().lower()
    q = (request.GET.get("q") or "").strip()

    tickets = (
        Ticket.objects.select_related("category", "user")
        .annotate(avg_rating=Coalesce(Avg("ratings__score"), 0.0))
        .annotate(rating_count=Count("ratings"))
    )

    if status in {Ticket.OPEN, Ticket.IN_PROGRESS, Ticket.CLOSED}:
        tickets = tickets.filter(status=status)
    if priority in {Ticket.LOW, Ticket.MEDIUM, Ticket.HIGH}:
        tickets = tickets.filter(priority=priority)
    if category:
        tickets = tickets.filter(category__slug=category)
    if q:
        tickets = tickets.filter(Q(subject__icontains=q) | Q(message__icontains=q))

    if sort == "oldest":
        tickets = tickets.order_by("created_at")
    elif sort == "rating_desc":
        tickets = tickets.order_by("-avg_rating", "-created_at")
    elif sort == "rating_asc":
        tickets = tickets.order_by("avg_rating", "-created_at")
    elif sort == "priority_desc":
        tickets = tickets.order_by("-priority", "-created_at")
    else:
        sort = "newest"
        tickets = tickets.order_by("-created_at")

    categories = Category.objects.order_by("name")
    return render(
        request,
        "complaints/admin_queue.html",
        {
            "tickets": tickets,
            "categories": categories,
            "filters": {
                "status": status,
                "priority": priority,
                "category": category,
                "sort": sort,
                "q": q,
            },
        },
    )


@login_required
@user_passes_test(_is_staff_user)
def admin_ticket_status(request, pk: int):
    if request.method != "POST":
        return redirect("admin_queue")

    ticket = get_object_or_404(Ticket, pk=pk)
    next_url = request.POST.get("next") or "admin_queue"
    new_status = (request.POST.get("status") or "").strip().lower()
    if new_status not in {Ticket.OPEN, Ticket.IN_PROGRESS, Ticket.CLOSED}:
        messages.error(request, "Invalid status.")
        return redirect(next_url)

    ticket.status = new_status
    ticket.save(update_fields=["status", "updated_at"])
    messages.success(request, f"Ticket #{ticket.id} status changed to {ticket.get_status_display()}.")
    return redirect(next_url)


def signup(request):
    if request.user.is_authenticated:
        return redirect("index")
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Account created.")
            return redirect("index")
    else:
        form = SignUpForm()
    return render(request, "registration/signup.html", {"form": form})


@login_required
def account(request):
    tickets = (
        Ticket.objects.filter(user=request.user)
        .select_related("category")
        .order_by("-created_at")
    )
    avg_rating = Ticket.objects.filter(user=request.user).aggregate(
        avg=Avg("ratings__score")
    )["avg"]
    rating_count = Ticket.objects.filter(user=request.user).aggregate(
        cnt=Count("ratings")
    )["cnt"]
    avatar_form = AvatarForm()
    profile, _ = Profile.objects.get_or_create(user=request.user)
    return render(
        request,
        "complaints/account.html",
        {
            "tickets": tickets,
            "avg_rating": avg_rating,
            "rating_count": rating_count,
            "avatar_form": avatar_form,
            "profile": profile,
        },
    )


@login_required
def upload_avatar(request):
    if request.method != "POST":
        return redirect("account")
    form = AvatarForm(request.POST, request.FILES)
    if form.is_valid():
        profile, _ = Profile.objects.get_or_create(user=request.user)
        profile.avatar = form.cleaned_data["avatar"]
        profile.save()
        messages.success(request, "Avatar updated.")
    else:
        messages.error(request, "Invalid image.")
    return redirect("account")


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
