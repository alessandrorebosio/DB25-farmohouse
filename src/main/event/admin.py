from django.contrib import admin
from django.db.models import Sum, F, IntegerField
from . import models


class EventSubscriptionInline(admin.TabularInline):
    model = models.EventSubscription
    extra = 0
    autocomplete_fields = ("user",)
    readonly_fields = ("user", "participants", "subscription_date")
    fields = ("user", "participants", "subscription_date")
    can_delete = False
    show_change_link = False


@admin.register(models.Event)
class EventAdmin(admin.ModelAdmin):
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

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            _taken=Sum("subscriptions__participants", output_field=IntegerField())
        )

    def taken(self, obj):
        return obj._taken or 0

    taken.short_description = "Booked"

    def remaining(self, obj):
        return (obj.seats or 0) - (obj._taken or 0)

    remaining.short_description = "Remaining"

    def created_by_display(self, obj):
        # Employee.username -> User (to_field username)
        return getattr(getattr(obj.created_by, "username", None), "username", "") or ""

    created_by_display.short_description = "Created by"
    created_by_display.admin_order_field = "created_by"
