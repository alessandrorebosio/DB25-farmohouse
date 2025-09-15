from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils.dateparse import parse_date
from .models import Service, Reservation, ReservationDetail
from .forms import BookingDateForm
from django.db.models import Count
from datetime import datetime, time


def service_list(request):
    """Search availability for Rooms and Restaurant."""
    # Rooms form params
    room_start_str = (request.GET.get("room_start") or "").strip()
    room_end_str = (request.GET.get("room_end") or "").strip()
    room_people_str = (request.GET.get("room_people") or "").strip()

    # Restaurant form params
    table_date_str = (request.GET.get("table_date") or "").strip()
    table_people_str = (request.GET.get("table_people") or "").strip()

    room_start = parse_date(room_start_str) if room_start_str else None
    room_end = parse_date(room_end_str) if room_end_str else None
    room_people = int(room_people_str) if room_people_str.isdigit() else None

    table_date = parse_date(table_date_str) if table_date_str else None
    table_people = int(table_people_str) if table_people_str.isdigit() else None

    available_rooms = []
    available_tables = []
    room_nights = None
    room_error = None
    table_error = None

    # Rooms availability
    if room_start and room_end and room_people:
        if room_end < room_start:
            room_error = "End date must be on or after start date."
        else:
            # nights: at least 1 if same-day check-in/out
            delta_days = (room_end - room_start).days
            room_nights = max(1, delta_days)
            start_dt = datetime.combine(room_start, time.min)
            end_dt = datetime.combine(room_end, time.max)

            reserved_room_ids = (
                ReservationDetail.objects.filter(
                    service__type="ROOM",
                    start_date__lte=end_dt,
                    end_date__gte=start_dt,
                )
                .values_list("service_id", flat=True)
                .distinct()
            )

            qs_rooms = (
                Service.objects.filter(
                    type="ROOM",
                    status="AVAILABLE",
                    room__max_capacity__gte=room_people,
                )
                .exclude(id__in=reserved_room_ids)
                .select_related("room")
                .order_by("id")
            )

            # attach total_price for convenience
            for s in qs_rooms:
                s.total_price = s.price * room_nights
            available_rooms = list(qs_rooms)

    # Restaurant availability (single day)
    if table_date and table_people:
        start_dt = datetime.combine(table_date, time.min)
        end_dt = datetime.combine(table_date, time.max)

        reserved_table_ids = (
            ReservationDetail.objects.filter(
                service__type="RESTAURANT",
                start_date__lte=end_dt,
                end_date__gte=start_dt,
            )
            .values_list("service_id", flat=True)
            .distinct()
        )

        available_tables = list(
            Service.objects.filter(
                type="RESTAURANT",
                status="AVAILABLE",
                restaurant__max_capacity__gte=table_people,
            )
            .exclude(id__in=reserved_table_ids)
            .select_related("restaurant")
            .order_by("id")
        )

    return render(
        request,
        "services.html",
        {
            "room_start": room_start,
            "room_end": room_end,
            "room_people": room_people,
            "room_nights": room_nights,
            "room_error": room_error,
            "available_rooms": available_rooms,
            "table_date": table_date,
            "table_people": table_people,
            "table_error": table_error,
            "available_tables": available_tables,
        },
    )


@login_required
def booking_confirm(request, service_id):
    service = get_object_or_404(Service, id=service_id)
    start_date = parse_date(request.session.get("booking_start_date") or "")
    end_date = parse_date(request.session.get("booking_end_date") or "")

    if not start_date or not end_date:
        return redirect("service:service_list")

    # Compute nights and total (rooms = nights, restaurant = 1 day)
    is_room = service.type == "ROOM"
    delta_days = (end_date - start_date).days
    nights = max(1, delta_days) if is_room else 1
    total_price = service.price * nights

    # Overlap check (prevent double booking for the selected period)
    start_dt = datetime.combine(start_date, time.min)
    end_dt = datetime.combine(end_date, time.max)
    overlap_exists = ReservationDetail.objects.filter(
        service=service, start_date__lte=end_dt, end_date__gte=start_dt
    ).exists()

    context = {
        "service": service,
        "start_date": start_date,
        "end_date": end_date,
        "booked": False,
        "is_room": is_room,
        "nights": nights,
        "total_price": total_price,
        "overlap_error": (
            "This service is no longer available for the selected dates."
            if overlap_exists
            else None
        ),
    }

    if request.method == "POST":
        if overlap_exists:
            return render(request, "booking_confirm.html", context)

        reservation = Reservation.objects.create(username_id=request.user.username)
        ReservationDetail.objects.create(
            reservation=reservation,
            service=service,
            start_date=start_dt,
            end_date=end_dt,
        )

        # Do not change service.status; availability is handled via ReservationDetail
        request.session.pop("booking_start_date", None)
        request.session.pop("booking_end_date", None)

        context["booked"] = True
        return render(request, "booking_confirm.html", context)

    return render(request, "booking_confirm.html", context)


@login_required
def quick_book(request, service_id):
    """
    Helper: set session dates from query params and redirect to booking_confirm.
    Accepts:
      - Rooms: ?start=YYYY-MM-DD&end=YYYY-MM-DD
      - Restaurant: ?date=YYYY-MM-DD (sets start=end=date)
    """
    service = get_object_or_404(Service, id=service_id)

    start_param = request.GET.get("start")
    end_param = request.GET.get("end")
    date_param = request.GET.get("date")

    start_date = None
    end_date = None

    if date_param:
        d = parse_date(date_param)
        if d:
            start_date = d
            end_date = d
    else:
        s = parse_date(start_param) if start_param else None
        e = parse_date(end_param) if end_param else None
        if s and e:
            start_date = s
            end_date = e

    if not start_date or not end_date:
        return redirect("service:service_list")

    request.session["booking_start_date"] = str(start_date)
    request.session["booking_end_date"] = str(end_date)

    return redirect("service:booking_confirm", service_id=service.id)
