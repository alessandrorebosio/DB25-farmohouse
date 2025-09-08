from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse
from django.db.models import F, Sum, DecimalField, Prefetch, ExpressionWrapper
from django.utils import timezone
from datetime import timedelta

from .forms import RegisterForm
from . import models
from product.models import Orders, OrderDetail
from event.models import EventSubscription


# Create your views here.
def register_view(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("login")
    else:
        form = RegisterForm()

    return render(request, "register.html", {"form": form})


def login_view(request: HttpRequest) -> HttpResponse:
    next_url = request.POST.get("next") or request.GET.get("next") or "/"
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect(next_url)
    else:
        form = AuthenticationForm(request)

    return render(request, "login.html", {"form": form, "next": next_url})


@login_required(login_url="login")
def profile_view(request: HttpRequest) -> HttpResponse:
    try:
        ut = models.User.objects.select_related("cf", "employee").get(
            username=request.user.username
        )
    except models.User.DoesNotExist:
        return render(
            request, "profile.html", {"query": None, "orders": [], "shifts": []}
        )

    query = {
        "employee": getattr(ut, "employee", None),
        "person": getattr(ut, "cf", None),
    }

    # Ordini dell’utente con righe e totali
    line_qs = (
        OrderDetail.objects.select_related("product")
        .annotate(
            line_total=ExpressionWrapper(
                F("quantity") * F("unit_price"),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            )
        )
        .order_by("product__name")
    )

    orders = (
        Orders.objects.filter(username_id=request.user.username)
        .annotate(
            order_total=Sum(
                ExpressionWrapper(
                    F("orderdetail__quantity") * F("orderdetail__unit_price"),
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                )
            )
        )
        .prefetch_related(
            Prefetch("orderdetail_set", queryset=line_qs, to_attr="lines")
        )
        .order_by("-date", "-id")
    )

    # Upcoming shifts (30 days) with fallback to recent
    shifts = []
    shifts_label = "Next 30 days"
    if query["employee"]:
        start = timezone.localdate()
        end = start + timedelta(days=30)
        upcoming = (
            models.EmployeeShift.objects.select_related("shift")
            .filter(
                employee_username=query["employee"],
                shift_date__range=(start, end),
            )
            .order_by("shift_date", "shift__start_time")
        )
        if upcoming.exists():
            shifts = list(upcoming)
            shifts_label = "Next 30 days"
        else:
            recent = (
                models.EmployeeShift.objects.select_related("shift")
                .filter(employee_username=query["employee"])
                .order_by("-shift_date", "-shift__start_time")[:20]
            )
            shifts = list(recent)
            shifts_label = "Recent shifts"

    subscriptions = (
        EventSubscription.objects.select_related("event")
        .filter(username_id=request.user.username)
        .order_by("event__event_date", "event__title")
    )
    today = timezone.localdate()

    return render(
        request,
        "profile.html",
        {
            "query": query,
            "orders": orders,
            "shifts": shifts,
            "shifts_label": shifts_label,
            "subscriptions": subscriptions,
            "today": today,
        },
    )


def logout_view(request: HttpRequest) -> HttpResponse:
    logout(request)
    return render(request, "index.html")
