from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils.dateparse import parse_date
from .models import Service, Reservation, ReservationDetail
from datetime import datetime, time, timedelta
from django.urls import reverse

# Slot di 2 ore per pasto
MEAL_START_TIMES = {
    "breakfast": time(8, 0),
    "lunch": time(12, 30),
    "dinner": time(19, 30),
}
MEAL_LABELS = {
    "breakfast": "Breakfast",
    "lunch": "Lunch",
    "dinner": "Dinner",
}


def get_meal_slot(date_obj, meal_key):
    start_t = MEAL_START_TIMES.get(meal_key)
    if not (date_obj and start_t):
        return None, None
    start_dt = datetime.combine(date_obj, start_t)
    end_dt = start_dt + timedelta(hours=2)
    return start_dt, end_dt


def service_list(request):
    room_start_str = (request.GET.get("room_start") or "").strip()
    room_end_str = (request.GET.get("room_end") or "").strip()
    room_people_str = (request.GET.get("room_people") or "").strip()

    table_date_str = (request.GET.get("table_date") or "").strip()
    table_people_str = (request.GET.get("table_people") or "").strip()
    table_meal = (request.GET.get("table_meal") or "").strip().lower()

    room_start = parse_date(room_start_str) if room_start_str else None
    room_end = parse_date(room_end_str) if room_end_str else None
    room_people = int(room_people_str) if room_people_str.isdigit() else None

    table_date = parse_date(table_date_str) if table_date_str else None
    table_people = int(table_people_str) if table_people_str.isdigit() else None
    if table_meal not in {"breakfast", "lunch", "dinner"}:
        table_meal = None

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

    # Restaurant availability (2-hour slot per meal)
    if table_date and table_people and table_meal:
        start_dt, end_dt = get_meal_slot(table_date, table_meal)

        reserved_table_ids = (
            ReservationDetail.objects.filter(
                service__type="RESTAURANT",
                # sovrapposizione su slot da 2 ore (consenti back-to-back)
                start_date__lt=end_dt,
                end_date__gt=start_dt,
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
        table_meal_label = MEAL_LABELS.get(table_meal)
    elif table_date and table_people and not table_meal:
        table_meal_label = None
        table_error = "Seleziona il pasto (Colazione, Pranzo o Cena)."
    else:
        table_meal_label = None

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
            "table_meal": table_meal,
            "table_meal_label": table_meal_label,
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
    meal_param = (request.GET.get("meal") or "").strip().lower()

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
        start_dt = datetime.combine(start_date, time(14, 0))
        end_base_date = (
            end_date if end_date > start_date else (start_date + timedelta(days=1))
        )
        end_dt = datetime.combine(end_base_date, time(10, 0))
        total_price = service.price * nights
        redirect_url = f"{reverse('service:service_list')}?room_start={start_date}&room_end={end_date}&room_people={people}"
        # Verifica overlap camere (includi sovrapposizioni)
        overlap_exists = ReservationDetail.objects.filter(
            service=service, start_date__lte=end_dt, end_date__gte=start_dt
        ).exists()
    else:
        # Ristorante: slot di 2 ore per il pasto
        if meal_param not in MEAL_START_TIMES:
            return redirect(
                f"{reverse('service:service_list')}?table_date={start_date}&table_people={people}"
            )
        start_dt, end_dt = get_meal_slot(start_date, meal_param)
        redirect_url = f"{reverse('service:service_list')}?table_date={start_date}&table_people={people}&table_meal={meal_param}"

        overlap_exists = ReservationDetail.objects.filter(
            service=service, start_date__lt=end_dt, end_date__gt=start_dt
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
