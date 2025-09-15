from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils.dateparse import parse_date
from .models import Service, Reservation, ReservationDetail
from .forms import BookingDateForm
from django.db.models import Count
from datetime import datetime


def service_list(request):
    """Show service types with available count, with search."""
    q = (request.GET.get("q") or "").strip()

    qs = Service.objects.filter(status="AVAILABLE")
    if q:
        qs = qs.filter(type__icontains=q)

    service_types = qs.values("type").annotate(count=Count("id")).order_by("type")

    return render(request, "services.html", {"service_types": service_types, "q": q})


@login_required
def service_type_booking(request, service_type):
    """Step 1: Choose start/end date for a service type."""
    if request.method == "POST":
        form = BookingDateForm(request.POST)
        if form.is_valid():
            start_date = form.cleaned_data["start_date"]
            end_date = form.cleaned_data["end_date"]

            # Save dates in session
            request.session["booking_start_date"] = str(start_date)
            request.session["booking_end_date"] = str(end_date)
            request.session["service_type"] = service_type

            return redirect("service:booking_results")
    else:
        form = BookingDateForm()

    return render(
        request,
        "service_type_booking.html",
        {"service_type": service_type, "form": form},
    )


@login_required
def booking_results(request):
    """Step 2: Show available services of the selected type in the given date range."""
    start_date = request.session.get("booking_start_date")
    end_date = request.session.get("booking_end_date")
    service_type = request.session.get("service_type")

    if not start_date or not end_date or not service_type:
        return redirect("service:service_list")

    start_date = parse_date(start_date)
    end_date = parse_date(end_date)

    # Services already booked (overlap) for the selected type
    reserved_services = ReservationDetail.objects.filter(
        Q(start_date__lte=end_date) & Q(end_date__gte=start_date),
        service__type=service_type,
    ).values_list("service_id", flat=True)

    # Services available of that type
    available_services = Service.objects.filter(
        type=service_type, status="AVAILABLE"
    ).exclude(id__in=reserved_services)

    return render(
        request,
        "booking_results.html",
        {
            "available_services": available_services,
            "start_date": start_date,
            "end_date": end_date,
            "service_type": service_type,
        },
    )


@login_required
def booking_confirm(request, service_id):
    service = get_object_or_404(Service, id=service_id)
    start_date = parse_date(request.session.get("booking_start_date"))
    end_date = parse_date(request.session.get("booking_end_date"))

    if request.method == "POST":
        reservation = Reservation.objects.create(username_id=request.user.username)

        ReservationDetail.objects.create(
            reservation=reservation,
            service=service,
            start_date=start_date,
            end_date=end_date,
        )
        service.status = "OCCUPIED"
        service.save()

        return render(
            request,
            "booking_confirm.html",
            {
                "service": service,
                "start_date": start_date,
                "end_date": end_date,
                "booked": True,  # flag for template
            },
        )

    return render(
        request,
        "booking_confirm.html",
        {
            "service": service,
            "start_date": start_date,
            "end_date": end_date,
            "booked": False,  # GET = not yet booked
        },
    )
