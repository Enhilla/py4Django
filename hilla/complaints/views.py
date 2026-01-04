from django.shortcuts import render, redirect, get_object_or_404
from .models import Complaint
from .forms import ComplaintForm


def index(request):
    # list all complaints (newest first)
    items = Complaint.objects.order_by("-created_at")
    return render(request, "complaints/index.html", {"items": items})


def create(request):
    # complaint submission page
    if request.method == "POST":
        form = ComplaintForm(request.POST)
        if form.is_valid():
            obj = form.save(commit=False)

            # attach user if logged in
            if request.user.is_authenticated:
                obj.user = request.user

            obj.save()
            return redirect("index")
    else:
        form = ComplaintForm()

    return render(request, "complaints/create.html", {"form": form})


def detail(request, pk: int):
    # optional: detail page
    c = get_object_or_404(Complaint, pk=pk)
    return render(request, "complaints/detail.html", {"c": c})
