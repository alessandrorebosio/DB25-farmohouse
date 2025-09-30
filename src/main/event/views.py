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


"""Views for the Event app.

Contains:
- event_view: list upcoming events with capacity and user-specific data
- book_event: book one or more seats for the current user (POST, auth)
- cancel_event: cancel the current user's booking (POST, auth)
"""


def event_view(request: HttpRequest) -> HttpResponse:
    """Render the events list with search and capacity annotations.

    Adds computed fields:
    - taken: total seats already booked across all subscriptions
    - remaining: seats still available (may be negative before max() in template)
    - my_participants: seats booked by the current user (0 if anonymous)

    SQL (approximate; actual SQL and quoting may vary by backend):

    SELECT
        E."id",
        E."seats",
        E."title",
        E."description",
        E."event_date",
        E."created_by",
        COALESCE(SUM(S."participants"), 0) AS "taken",
        E."seats" - COALESCE(SUM(S."participants"), 0) AS "remaining",
        COALESCE(SUM(CASE WHEN S."user" = %s THEN S."participants" ELSE 0 END), 0) AS "my_participants"
    FROM "EVENT" E
    LEFT OUTER JOIN "EVENT_SUBSCRIPTION" S ON (S."event" = E."id")
    WHERE E."event_date" >= %s
    GROUP BY E."id", E."seats", E."title", E."description", E."event_date", E."created_by"
    ORDER BY E."event_date" ASC, E."title" ASC;
    """
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
                    filter=Q(subscriptions__user_id=request.user.username),
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
    """Book one or more seats for the current authenticated user.

    Validates input, enforces capacity using row locks (SELECT ... FOR UPDATE)
    to avoid race conditions, then inserts/updates the user's subscription.

    SQL (approximate; executed within a transaction):

    -- Fetch target event
    SELECT E.*
    FROM "EVENT" E
    WHERE E."id" = %s
    LIMIT 1;

    -- Lock all subscriptions for this event and compute taken seats
    SELECT COALESCE(SUM(S."participants"), 0) AS "taken"
    FROM "EVENT_SUBSCRIPTION" S
    WHERE S."event" = %s
    FOR UPDATE;

    -- Find existing subscription for the current user (row-level lock)
    SELECT S.*
    FROM "EVENT_SUBSCRIPTION" S
    WHERE S."event" = %s AND S."user" = %s
    LIMIT 1
    FOR UPDATE;

    -- If exists: increment participants
    UPDATE "EVENT_SUBSCRIPTION"
    SET "participants" = "participants" + %s
    WHERE "event" = %s AND "user" = %s;

    -- Else: create a new subscription
    INSERT INTO "EVENT_SUBSCRIPTION" ("event", "user", "subscription_date", "participants")
    VALUES (%s, %s, %s, %s);
    """
    event = get_object_or_404(Event, pk=event_id)

    subs_qs = EventSubscription.objects.select_for_update().filter(event=event)

    try:
        participants = int(request.POST.get("participants", "0"))
    except ValueError:
        participants = 0
    if participants <= 0:
        messages.error(request, "Invalid number of participants.")
        return redirect(request.POST.get("next") or "event_list")

    taken = subs_qs.aggregate(taken=Coalesce(Sum("participants"), 0))["taken"]
    remaining = event.seats - taken

    if remaining <= 0:
        messages.error(request, "Event is fully booked.")
        return redirect(request.POST.get("next") or "event_list")
    if participants > remaining:
        messages.error(request, f"You can book at most {remaining} more.")
        return redirect(request.POST.get("next") or "event_list")

    sub = subs_qs.filter(user_id=request.user.username).first()

    if sub:
        sub.participants += participants
        sub.save(update_fields=["participants"])
        messages.success(
            request,
            f"Added {participants} participant{'s' if participants != 1 else ''} to your booking for '{event.title}'.",
        )
    else:
        EventSubscription.objects.create(
            event=event,
            user_id=request.user.username,
            subscription_date=timezone.now(),
            participants=participants,
        )
        messages.success(
            request,
            f"Booked {participants} participant{'s' if participants != 1 else ''} for '{event.title}'.",
        )
    return redirect(request.POST.get("next") or "event_list")


@login_required
@require_POST
@transaction.atomic
def cancel_event(request: HttpRequest, event_id: int) -> HttpResponse:
    """Cancel the current user's booking for a future event.

    Protects past events from cancellation and uses row-level locking to
    ensure consistent state when deleting the subscription.

    SQL (approximate; executed within a transaction):

    -- Fetch target event
    SELECT E.*
    FROM "EVENT" E
    WHERE E."id" = %s
    LIMIT 1;

    -- Lock current user's subscription row if it exists
    SELECT S.*
    FROM "EVENT_SUBSCRIPTION" S
    WHERE S."event" = %s AND S."user" = %s
    LIMIT 1
    FOR UPDATE;

    -- Delete the subscription (freeing capacity)
    DELETE FROM "EVENT_SUBSCRIPTION"
    WHERE "event" = %s AND "user" = %s;
    """
    event = get_object_or_404(Event, pk=event_id)

    if event.event_date < timezone.localdate():
        messages.error(request, "Event already in the past; cannot cancel.")
        return redirect(request.POST.get("next") or "event_list")

    sub = (
        EventSubscription.objects.select_for_update()
        .filter(event=event, user_id=request.user.username)
        .first()
    )
    if not sub:
        messages.error(request, "No booking to cancel.")
        return redirect(request.POST.get("next") or "event_list")

    canceled = sub.participants or 0
    title = event.title
    sub.delete()
    messages.success(
        request,
        f"Canceled your booking ({canceled} participant{'s' if canceled != 1 else ''}) for '{title}'.",
    )
    return redirect(request.POST.get("next") or "event_list")
