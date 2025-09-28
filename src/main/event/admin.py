"""Admin configuration for the Event app.

This module defines Django Admin classes and inlines to manage events and
their subscriptions efficiently. It adds computed columns (booked/remaining),
avoids N+1 queries, and keeps the UI compact and searchable.
"""

from django.contrib import admin
from django.db.models import Sum, IntegerField
from django.db.models.functions import Coalesce
from . import models


class EventSubscriptionInline(admin.TabularInline):
    """Inline table showing subscriptions linked to an event.

    - Read-only to prevent accidental edits from the Event page.
    - No extra blank rows to keep the UI clean.
    - Autocomplete on user for faster lookups.
    """

    model = models.EventSubscription
    extra = 0
    autocomplete_fields = ("user",)
    readonly_fields = ("user", "participants", "subscription_date")
    fields = ("user", "participants", "subscription_date")
    can_delete = False
    show_change_link = False


@admin.register(models.Event)
class EventAdmin(admin.ModelAdmin):
    """Admin configuration for events.

    Provides:
    - Computed columns: Booked and Remaining seats
    - Filters, search, ordering
    - Inline list of subscriptions (read-only)
    - Query optimizations to avoid N+1 when rendering the list
    """

    list_display = (
        "title",
        "event_date",
        "seats",
        "taken",
        "remaining",
        "created_by_display",
    )
    list_filter = ("event_date",)
    search_fields = ("title", "description", "created_by__username__username")
    ordering = ("event_date", "title")
    inlines = [EventSubscriptionInline]
    autocomplete_fields = ("created_by",)
    list_select_related = ("created_by", "created_by__username")
    list_per_page = 25

    def get_queryset(self, request):
        """Return queryset annotated with computed fields and optimized joins.

        - _taken: total booked participants for the event (coalesced to 0)
        - Uses select_related for created_by and nested username to avoid
          additional queries when rendering display columns.
        """
        qs = (
            super()
            .get_queryset(request)
            .select_related("created_by", "created_by__username")
        )
        return qs.annotate(
            _taken=Coalesce(
                Sum("subscriptions__participants"), 0, output_field=IntegerField()
            )
        )

    @admin.display(description="Booked", ordering="_taken")
    def taken(self, obj):
        """Total number of booked seats for this event."""
        return obj._taken

    @admin.display(description="Remaining")
    def remaining(self, obj):
        """Seats still available (never negative)."""
        seats = obj.seats or 0
        taken = obj._taken or 0
        return max(0, seats - taken)

    @admin.display(description="Created by", ordering="created_by")
    def created_by_display(self, obj):
        """Human-friendly creator name (User.username via Employee)."""
        return getattr(getattr(obj.created_by, "username", None), "username", "") or ""
