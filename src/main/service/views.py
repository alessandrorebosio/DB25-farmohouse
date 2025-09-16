from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils.dateparse import parse_date
from .models import Service, Reservation, ReservationDetail
from datetime import datetime, time, timedelta
from django.urls import reverse


def service_list(request):
    room_start_str = (request.GET.get("room_start") or "").strip()
    room_end_str = (request.GET.get("room_end") or "").strip()
    room_people_str = (request.GET.get("room_people") or "").strip()

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

    try:
        people = int(people_param) if people_param is not None else 1
        if people <= 0:
            people = 1
    except ValueError:
        people = 1

    is_room = service.type == "ROOM"

    if is_room:
        delta_days = (end_date - start_date).days
        nights = max(1, delta_days)
        start_dt = datetime.combine(start_date, time(14, 0))  # check-in 14:00
        end_base_date = (
            end_date if end_date > start_date else (start_date + timedelta(days=1))
        )
        end_dt = datetime.combine(end_base_date, time(10, 0))  # check-out 10:00
        total_price = service.price * nights
        redirect_url = f"{reverse('service:service_list')}?room_start={start_date}&room_end={end_date}&room_people={people}"
    else:
        start_dt = datetime.combine(start_date, time.min)
        end_dt = datetime.combine(end_date, time.max)
        total_price = service.price
        redirect_url = f"{reverse('service:service_list')}?table_date={start_date}&table_people={people}"

    overlap_exists = ReservationDetail.objects.filter(
        service=service, start_date__lte=end_dt, end_date__gte=start_dt
    ).exists()

    if overlap_exists:
        return redirect(redirect_url)

    reservation = Reservation.objects.create(username_id=request.user.username)
    ReservationDetail.objects.create(
        reservation=reservation,
        service=service,
        start_date=start_dt,
        end_date=end_dt,
        people=people,
    )

    return redirect(redirect_url)
