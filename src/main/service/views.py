from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_POST
from django.contrib import messages

from django.utils import timezone
from .models import Service, Reservation, ReservationDetail
from datetime import datetime, time, timedelta
from django.db import transaction


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
                    room__max_capacity__gte=room_people,
                )
                .exclude(id__in=reserved_room_ids)
                .select_related("room")
                .order_by("id")
            )

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
def quick_book(request, service_id):
    """
    Accepts:
      - Rooms: ?start=YYYY-MM-DD&end=YYYY-MM-DD&people=INT
      - Restaurant: ?date=YYYY-MM-DD&people=INT (sets start=end=date)
    Saves dates and people in session then redirects to booking_confirm.
    """
    service = get_object_or_404(Service, id=service_id)

    start_param = request.GET.get("start")
    end_param = request.GET.get("end")
    date_param = request.GET.get("date")
    people_param = request.GET.get("people")

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

    # people
    try:
        ppl = int(people_param) if people_param is not None else 1
        if ppl <= 0:
            ppl = 1
    except ValueError:
        ppl = 1
    request.session["booking_people"] = ppl

    return redirect("service:booking_confirm", service_id=service.id)


@login_required
def booking_confirm(request, service_id):
    service = get_object_or_404(Service, id=service_id)
    start_date = parse_date(request.session.get("booking_start_date") or "")
    end_date = parse_date(request.session.get("booking_end_date") or "")
    people = request.session.get("booking_people") or 1
    try:
        people = int(people)
        if people <= 0:
            people = 1
    except (TypeError, ValueError):
        people = 1

    if not start_date or not end_date:
        return redirect("service:service_list")

    is_room = service.type == "ROOM"
    delta_days = (end_date - start_date).days
    nights = max(1, delta_days) if is_room else 1
    total_price = service.price * nights

    # Apply check-in/out times
    if is_room:
        start_dt = datetime.combine(start_date, time(14, 0))  # 14:00 check-in
        # ensure checkout is at least next day if same/earlier date is passed
        end_base_date = (
            end_date if end_date > start_date else (start_date + timedelta(days=1))
        )
        end_dt = datetime.combine(end_base_date, time(10, 0))  # 10:00 check-out
    else:
        # keep full-day window for restaurant bookings
        start_dt = datetime.combine(start_date, time.min)
        end_dt = datetime.combine(end_date, time.max)

    overlap_exists = ReservationDetail.objects.filter(
        service=service, start_date__lte=end_dt, end_date__gte=start_dt
    ).exists()

    context = {
        "service": service,
        "start_date": start_date,
        "end_date": end_date,
        "people": people,
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
            people=people,
        )

        request.session.pop("booking_start_date", None)
        request.session.pop("booking_end_date", None)
        request.session.pop("booking_people", None)

        context["booked"] = True
        return render(request, "booking_confirm.html", context)

    return render(request, "booking_confirm.html", context)

@login_required
@require_POST
@transaction.atomic
def cancel_reservation(request, reservation_id):  # Deve essere reservation_id
    """
    Cancel a Reservation
    """
    
    reservation_details = ReservationDetail.objects.filter(reservation_id=reservation_id)
    
    # Verify that the user is the author of the reservation
    if not reservation_details.exists() or reservation_details.first().reservation.username_id != request.user.username:
        messages.error(request, "You can only cancel your own reservations.")
        return redirect(request.POST.get("next") or "profile")
    
    # Check if reservation has started
    if reservation_details.first().start_date < timezone.now():
        messages.error(request, "Cannot cancel a reservation that has already started.")
        return redirect(request.POST.get("next") or "profile")
    
    # delete all details
    reservation_details.delete()

    try:
        reservation = Reservation.objects.get(id=reservation_id)
        if not reservation.details.exists():
            reservation.delete()
    except Reservation.DoesNotExist:
        pass
    
    messages.success(request, "Reservation cancelled successfully.")
    return redirect(request.POST.get("next") or "profile")