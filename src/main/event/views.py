from django.db.models import Q, F, Sum, IntegerField
from django.db.models.functions import Coalesce
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpRequest, HttpResponse
from django.db import transaction

from .models import Event, EventSubscription


def event_view(request: HttpRequest) -> HttpResponse:
    q = (request.GET.get("q") or "").strip()
    today = timezone.localdate()
    qs = (
        Event.objects.select_related("created_by")
        .filter(event_date__gte=today)
        .annotate(
            taken=Coalesce(
                Sum("subscriptions__participants"), 0, output_field=IntegerField()
            ),
            remaining=F("seats")
            - Coalesce(
                Sum("subscriptions__participants"), 0, output_field=IntegerField()
            ),
            my_participants=Coalesce(
                Sum(
                    "subscriptions__participants",
                    filter=Q(subscriptions__username_id=request.user.username),
                ),
                0,
                output_field=IntegerField(),
            ),
        )
        .order_by("event_date", "title")
    )
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))
    return render(request, "events.html", {"events": qs, "q": q})


@login_required
@require_POST
@transaction.atomic
def book_event(request: HttpRequest, event_id: int) -> HttpResponse:
    event = get_object_or_404(Event, pk=event_id)

    EventSubscription.objects.select_for_update().filter(event=event)

    try:
        participants = int(request.POST.get("participants", "0"))
    except ValueError:
        participants = 0
    if participants <= 0:
        messages.error(request, "Invalid number of participants.")
        return redirect(request.POST.get("next") or "event_list")

    taken = EventSubscription.objects.filter(event=event).aggregate(
        taken=Coalesce(Sum("participants"), 0)
    )["taken"]
    remaining = event.seats - taken

    if remaining <= 0:
        messages.error(request, "Event is fully booked.")
        return redirect(request.POST.get("next") or "event_list")
    if participants > remaining:
        messages.error(request, f"You can book at most {remaining} more.")
        return redirect(request.POST.get("next") or "event_list")

    sub = EventSubscription.objects.filter(
        event=event, username_id=request.user.username
    ).first()

    if sub:
        sub.participants += participants
        sub.save(update_fields=["participants"])
    else:
        EventSubscription.objects.create(
            event=event,
            username_id=request.user.username,
            subscription_date=timezone.now(),
            participants=participants,
        )
    return redirect(request.POST.get("next") or "event_list")


@login_required
@require_POST
@transaction.atomic
def cancel_event(request: HttpRequest, event_id: int) -> HttpResponse:
    event = get_object_or_404(Event, pk=event_id)

    # cannot cancel past events
    if event.event_date < timezone.localdate():
        messages.error(request, "Event already in the past; cannot cancel.")
        return redirect(request.POST.get("next") or "event_list")

    sub = (
        EventSubscription.objects.select_for_update()
        .filter(event=event, username_id=request.user.username)
        .first()
    )
    if not sub:
        messages.error(request, "No booking to cancel.")
        return redirect(request.POST.get("next") or "event_list")

    sub.delete()  # freeing seats automatically (capacity is derived)
    return redirect(request.POST.get("next") or "event_list")
