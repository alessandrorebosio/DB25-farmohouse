from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse
from django.db.models import (
    F,
    Sum,
    DecimalField,
    Prefetch,
    ExpressionWrapper,
    Count,
)
from decimal import Decimal
from django.utils import timezone
from datetime import datetime, time,timedelta

from .forms import RegisterForm
from . import models
from product.models import Orders, OrderDetail
from event.models import EventSubscription
from service.models import Reservation, ReservationDetail, Service


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

def _ensure_datetime(value):
    """Return a timezone-aware datetime from a date or datetime, or None."""
    if value is None:
        return None
    if isinstance(value, datetime):
        # if naive, makes aware
        if timezone.is_naive(value):
            return timezone.make_aware(value, timezone.get_current_timezone())
        return value
    # instance of date (but not datetime)
    dt = datetime.combine(value, time.min)
    return timezone.make_aware(dt, timezone.get_current_timezone())


@login_required(login_url="login")
def profile_view(request: HttpRequest) -> HttpResponse:
    now = timezone.now()
    today = timezone.localdate()

    try:
        ut = models.User.objects.select_related("cf", "employee").get(
            username=request.user.username
        )
    except models.User.DoesNotExist:
        return render(
            request,
            "profile.html",
            {"query": None, "orders": [], "shifts": [], "reservations": []},
        )

    query = {
        "employee": getattr(ut, "employee", None),
        "person": getattr(ut, "cf", None),
    }

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
        .filter(user_id=request.user.username)
        .order_by("event__event_date", "event__title")
    )
    for s in subscriptions:
        ev_date = getattr(s.event, "event_date", None)
        if isinstance(ev_date, datetime):
            s.can_review = _ensure_datetime(ev_date) <= now
        else:
            s.can_review = (ev_date is not None) and (ev_date < today)


    reservations = (
        Reservation.objects.filter(username_id=request.user.username)
        .prefetch_related(
            Prefetch(
                "details",
                queryset=ReservationDetail.objects.select_related(
                    "service", "service__room", "service__restaurant"
                ).order_by("start_date"),
                to_attr="reservation_details",
            )
        )
        .order_by("-reservation_date")
    )

    for r in reservations:
        total = Decimal("0.00")
        for d in r.reservation_details:
            svc = d.service
            d.is_room = svc.type == "ROOM"
            
            
            start_dt = _ensure_datetime(d.start_date)
            end_dt = _ensure_datetime(d.end_date)
            # can_review: fine prenotazione passata
            d.can_review = (end_dt is not None) and (end_dt <= now)

            # can_cancel: start > now + 7 giorni
            d.can_cancel = (start_dt is not None) and ((start_dt - now) > timedelta(days=7))

            # in_no_action_window: tra 0 e 7 giorni
            d.in_no_action_window = (start_dt is not None) and (timedelta(0) <= (start_dt - now) <= timedelta(days=7))
            
            # Notti: (end.date - start.date).days, niente +1; minimo 1 solo per camere
            start_d = d.start_date.date()
            end_d = d.end_date.date()
            nights = (end_d - start_d).days if d.is_room else 1
            if d.is_room and nights <= 0:
                nights = 1

            d.nights = nights
            d.total_price = (svc.price or Decimal("0.00")) * nights
            total += d.total_price

        r.total_price = total

    return render(
        request,
        "profile.html",
        {
            "query": query,
            "orders": orders,
            "shifts": shifts,
            "shifts_label": shifts_label,
            "subscriptions": subscriptions,
            "reservations": reservations,
            "today": timezone.localdate(),
        },
    )


def logout_view(request: HttpRequest) -> HttpResponse:
    logout(request)
    return render(request, "index.html")


def statistic_view(request: HttpRequest) -> HttpResponse:
    # Simple KPI counts
    users_count = models.User.objects.count()
    employees_count = models.Employee.objects.count()
    orders_count = Orders.objects.count()

    # Total revenue from order details (quantity * unit_price)
    revenue = OrderDetail.objects.annotate(
        line_total=ExpressionWrapper(
            F("quantity") * F("unit_price"),
            output_field=DecimalField(max_digits=12, decimal_places=2),
        )
    ).aggregate(total=Sum("line_total")).get("total") or Decimal("0.00")

    # Reservations count
    reservations_count = Reservation.objects.count()

    # Top services by number of reservation details (bookings)
    top_services_qs = (
        ReservationDetail.objects.values(
            "service",
            "service__type",
            "service__room__code",
            "service__restaurant__code",
        )
        .annotate(bookings=Count("service"))
        .order_by("-bookings")[:10]
    )

    # Build display name for each service (ROOM/RESTAURANT may have a code)
    top_services = []
    for s in top_services_qs:
        code = s.get("service__room__code") or s.get("service__restaurant__code")
        svc_type = s.get("service__type")
        display = f"{svc_type.title()}"
        if code:
            display += f" · {code}"
        else:
            display += f" · ID {s.get('service')}"
        top_services.append(
            {
                "service_id": s.get("service"),
                "type": svc_type,
                "name": display,
                "bookings": s.get("bookings", 0),
            }
        )

    # Top products by quantity and by revenue
    top_products_qty = (
        OrderDetail.objects.values("product", "product__name")
        .annotate(total_qty=Sum("quantity"))
        .order_by("-total_qty")[:10]
    )

    top_products_rev = (
        OrderDetail.objects.annotate(
            line_total=ExpressionWrapper(
                F("quantity") * F("unit_price"),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            )
        )
        .values("product", "product__name")
        .annotate(total_revenue=Sum("line_total"))
        .order_by("-total_revenue")[:10]
    )

    # Top events by total participants
    top_events = (
        EventSubscription.objects.values("event", "event__title", "event__event_date")
        .annotate(total_participants=Sum("participants"))
        .order_by("-total_participants", "event__event_date")[:10]
    )

    context = {
        "kpis": {
            "users": users_count,
            "employees": employees_count,
            "orders": orders_count,
            "revenue": revenue,
            "reservations": reservations_count,
        },
        "top_services": top_services,
        "top_products_qty": top_products_qty,
        "top_products_rev": top_products_rev,
        "top_events": top_events,
        "today": timezone.localdate(),
    }

    return render(request, "statistic.html", context)
