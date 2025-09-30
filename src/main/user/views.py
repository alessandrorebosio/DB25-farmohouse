"""Views for the User app.

Contains:
- register_view: create Person + User records via RegisterForm
- login_view: authenticate using Django form and custom backend
- profile_view: show orders, shifts, event subscriptions, reservations
- statistic_view: staff-only counters for quick stats
- logout_view: end session and render homepage

The style mirrors the Event app with succinct explanations and inline hints.
"""

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
    Case,
    When,
    Value,
    IntegerField,
)
from decimal import Decimal
from django.utils import timezone
from datetime import datetime, time, timedelta

from .forms import RegisterForm
from . import models
from product.models import Orders, OrderDetail
from event.models import EventSubscription
from service.models import Booking, BookingDetail, Service
from django.contrib.admin.views.decorators import staff_member_required
from django.db.models.functions import TruncDate, Greatest
from django.db.models.expressions import Func


def register_view(request: HttpRequest) -> HttpResponse:
    """Render and process the user registration form.

    On success, creates both Person and User (see forms.RegisterForm.save)
    and redirects to the login page.

    SQL (approximate; executed by the form's save method):

    SELECT P.*
    FROM "PERSON" P
    WHERE P."cf" = %s
    LIMIT 1;

    INSERT INTO "PERSON" ("cf", "name", "surname")
    VALUES (%s, %s, %s)
    ON CONFLICT ("cf") DO NOTHING;  -- backend-dependent

    INSERT INTO "USER" ("username", "cf", "email", "password")
    VALUES (%s, %s, %s, %s);
    """
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("login")
    else:
        form = RegisterForm()

    return render(request, "register.html", {"form": form})


def login_view(request: HttpRequest) -> HttpResponse:
    """Render and process the login form using Django's AuthenticationForm.

    Uses the project's custom authentication backend to map app users to
    Django auth users. Respects an optional "next" redirect parameter.

    SQL (approximate; executed by the custom auth backend):

    SELECT U.*
    FROM "USER" U
    WHERE U."username" = %s
    LIMIT 1;

    SELECT 1
    FROM "active_employees"
    WHERE "username" = %s
    LIMIT 1;

    SELECT E."role"
    FROM "EMPLOYEE" E
    WHERE E."username" = %s
    LIMIT 1;

    -- Mirror to auth_user (insert or update)
    SELECT AU.*
    FROM "auth_user" AU
    WHERE AU."username" = %s
    LIMIT 1;

    INSERT INTO "auth_user" ("username", "email", "is_staff", "is_superuser", "is_active", "password", "first_name", "last_name", "date_joined")
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
    """
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
    """Return a timezone-aware datetime from a date or datetime, or None.

    - If value is already an aware datetime, return as-is
    - If value is a naive datetime, make it aware in the current timezone
    - If value is a date, convert to start-of-day aware datetime
    - If None, return None
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        if timezone.is_naive(value):
            return timezone.make_aware(value, timezone.get_current_timezone())
        return value

    dt = datetime.combine(value, time.min)
    return timezone.make_aware(dt, timezone.get_current_timezone())


@login_required(login_url="login")
def profile_view(request: HttpRequest) -> HttpResponse:
    """Show the user's dashboard: orders, shifts, event subscriptions, bookings.

    Queries:
    - Orders with prefetch of lines and computed order_total
    - Shifts (next 30 days if any; else recent last 20)
    - Event subscriptions with a computed flag `can_review`
    - Reservations with details and computed pricing/cancellation flags

    SQL (approximate; actual SQL and quoting vary by backend):

    SELECT U."username", U."email", P."cf", P."name", P."surname", E."role"
    FROM "USER" U
    LEFT JOIN "PERSON" P ON P."cf" = U."cf"
    LEFT JOIN "EMPLOYEE" E ON E."username" = U."username"
    WHERE U."username" = %s
    LIMIT 1;

    SELECT O."id", O."date",
           SUM(OD."quantity" * OD."unit_price") AS order_total
    FROM "ORDERS" O
    LEFT JOIN "ORDER_DETAIL" OD ON OD."order_id" = O."id"
    WHERE O."username" = %s
    GROUP BY O."id", O."date"
    ORDER BY O."date" DESC, O."id" DESC;

    SELECT OD.*
    FROM "ORDER_DETAIL" OD
    WHERE OD."order_id" IN (...);

    SELECT ES."employee_username", ES."shift_date", S."shift_name", S."day", S."start_time", S."end_time"
    FROM "EMPLOYEE_SHIFT" ES
    JOIN "SHIFT" S ON S."id" = ES."shift_id"
    WHERE ES."employee_username" = %s AND ES."shift_date" BETWEEN %s AND %s
    ORDER BY ES."shift_date" ASC, S."start_time" ASC;

    SELECT ES."employee_username", ES."shift_date", S."shift_name", S."day", S."start_time", S."end_time"
    FROM "EMPLOYEE_SHIFT" ES
    JOIN "SHIFT" S ON S."id" = ES."shift_id"
    WHERE ES."employee_username" = %s
    ORDER BY ES."shift_date" DESC, S."start_time" DESC
    LIMIT 20;

    SELECT ES.*
    FROM "EVENT_SUBSCRIPTION" ES
    JOIN "EVENT" E ON E."id" = ES."event"
    WHERE ES."user" = %s
    ORDER BY E."event_date" ASC, E."title" ASC;

    SELECT B.*
    FROM "BOOKING" B
    WHERE B."username" = %s
    ORDER BY B."booking_date" DESC;

    SELECT BD.*, SV.*
    FROM "BOOKING_DETAIL" BD
    JOIN "SERVICE" SV ON SV."id" = BD."service"
    WHERE BD."booking" IN (...)
    ORDER BY BD."start_date" ASC;
    """
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
            {"query": None, "orders": [], "shifts": [], "bookings": []},
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

    bookings = (
        Booking.objects.filter(username_id=request.user.username)
        .prefetch_related(
            Prefetch(
                "details",
                queryset=BookingDetail.objects.select_related(
                    "service", "service__room", "service__restaurant"
                ).order_by("start_date"),
                to_attr="booking_details",
            )
        )
        .order_by("-booking_date")
    )

    for r in bookings:
        total = Decimal("0.00")
        for d in r.booking_details:
            svc = d.service
            d.is_room = svc.type == "ROOM"

            start_dt = _ensure_datetime(d.start_date)
            end_dt = _ensure_datetime(d.end_date)
            d.can_review = (end_dt is not None) and (end_dt <= now)

            d.can_cancel = (start_dt is not None) and (
                (start_dt - now) > timedelta(days=7)
            )

            d.in_no_action_window = (start_dt is not None) and (
                timedelta(0) <= (start_dt - now) <= timedelta(days=7)
            )

            start_d = d.start_date.date()
            end_d = d.end_date.date()
            nights = (end_d - start_d).days if d.is_room else 1
            if d.is_room and nights <= 0:
                nights = 1

            d.nights = nights
            price = getattr(d, "unit_price", None)
            if price is None:
                price = svc.price or Decimal("0.00")
            d.total_price = price * nights
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
            "bookings": bookings,
            "today": timezone.localdate(),
        },
    )


def logout_view(request: HttpRequest) -> HttpResponse:
    """
    Log out and render the homepage template.
    """
    logout(request)
    return render(request, "index.html")


@staff_member_required(login_url="/login")
def statistic_view(request: HttpRequest) -> HttpResponse:
    """Simple staff-only statistics counters for users, employees and orders.

    SQL (approximate):

    SELECT COUNT(*) FROM "USER";
    SELECT COUNT(*) FROM "EMPLOYEE";
    SELECT COUNT(*) FROM "ORDERS";

    SELECT SUM(OD."quantity" * OD."unit_price") AS revenue
    FROM "ORDER_DETAIL" OD;

    SELECT COUNT(*) FROM "BOOKING";

    SELECT BD."service", SV."type", SV."room_id", SV."restaurant_id", COUNT(*) AS bookings
    FROM "BOOKING_DETAIL" BD
    JOIN "SERVICE" SV ON SV."id" = BD."service"
    GROUP BY BD."service", SV."type", SV."room_id", SV."restaurant_id"
    ORDER BY bookings DESC
    LIMIT 10;

    SELECT OD."product_id", P."name", SUM(OD."quantity") AS total_qty
    FROM "ORDER_DETAIL" OD
    JOIN "PRODUCT" P ON P."id" = OD."product_id"
    GROUP BY OD."product_id", P."name"
    ORDER BY total_qty DESC
    LIMIT 10;

    SELECT OD."product_id", P."name", SUM(OD."quantity" * OD."unit_price") AS total_revenue
    FROM "ORDER_DETAIL" OD
    JOIN "PRODUCT" P ON P."id" = OD."product_id"
    GROUP BY OD."product_id", P."name"
    ORDER BY total_revenue DESC
    LIMIT 10;

    SELECT ES."event", E."title", E."event_date", SUM(ES."participants") AS total_participants
    FROM "EVENT_SUBSCRIPTION" ES
    JOIN "EVENT" E ON E."id" = ES."event"
    GROUP BY ES."event", E."title", E."event_date"
    ORDER BY total_participants DESC, E."event_date" ASC
    LIMIT 10;

    SELECT * FROM "fully_booked_events" ORDER BY "event_date" DESC LIMIT 50;
    SELECT * FROM "free_services_now" ORDER BY "available" DESC, "type" ASC, "service_id" ASC LIMIT 200;
    """
    users_count = models.User.objects.count()
    employees_count = models.Employee.objects.count()
    orders_count = Orders.objects.count()

    product_revenue = OrderDetail.objects.annotate(
        line_total=ExpressionWrapper(
            F("quantity") * F("unit_price"),
            output_field=DecimalField(max_digits=12, decimal_places=2),
        )
    ).aggregate(total=Sum("line_total")).get("total") or Decimal("0.00")

    # For rooms, revenue should consider number of nights (at least 1).
    # For restaurants, keep existing behavior (people * unit_price).
    nights_expr = Case(
        When(
            service__type="ROOM",
            then=Greatest(
                Value(1),
                Func(
                    TruncDate("end_date"), TruncDate("start_date"), function="DATEDIFF"
                ),
            ),
        ),
        default=Value(1),
        output_field=IntegerField(),
    )

    booking_revenue = BookingDetail.objects.annotate(nights=nights_expr).annotate(
        line_total=Case(
            When(
                service__type="ROOM",
                then=ExpressionWrapper(
                    F("unit_price") * F("nights"),
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                ),
            ),
            default=ExpressionWrapper(
                F("people") * F("unit_price"),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            ),
            output_field=DecimalField(max_digits=12, decimal_places=2),
        )
    ).aggregate(total=Sum("line_total")).get("total") or Decimal("0.00")

    revenue = (product_revenue or Decimal("0.00")) + (
        booking_revenue or Decimal("0.00")
    )

    bookings_count = Booking.objects.count()

    top_services_qs = (
        BookingDetail.objects.values(
            "service",
            "service__type",
            "service__room__code",
            "service__restaurant__code",
        )
        .annotate(bookings=Count("service"))
        .order_by("-bookings")[:10]
    )

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

    top_events = (
        EventSubscription.objects.values("event", "event__title", "event__event_date")
        .annotate(total_participants=Sum("participants"))
        .order_by("-total_participants", "event__event_date")[:10]
    )

    fully_booked_qs = models.FullyBookedEvent.objects.all().order_by("-event_date")[:50]
    free_services_qs = models.FreeServiceNow.objects.all().order_by(
        "-available", "type", "service_id"
    )[:200]

    context = {
        "kpis": {
            "users": users_count,
            "employees": employees_count,
            "orders": orders_count,
            "revenue": revenue,
            "bookings": bookings_count,
        },
        "top_services": top_services,
        "top_products_qty": top_products_qty,
        "top_products_rev": top_products_rev,
        "top_events": top_events,
        "fully_booked_events": fully_booked_qs,
        "free_services_now": free_services_qs,
        "today": timezone.localdate(),
    }

    return render(request, "statistic.html", context)
