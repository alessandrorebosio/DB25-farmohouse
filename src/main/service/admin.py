"""Admin configuration for Services and Booking.

This improves display helpers, pagination, and inline filtering to show only the
relevant inline (Restaurant or Room) based on Service.type.
"""

from django.contrib import admin
from .models import Booking, Service, Restaurant, Room


class RestaurantInline(admin.StackedInline):
    model = Restaurant
    extra = 0
    can_delete = True
    fields = ("code", "max_capacity")
    show_change_link = False


class RoomInline(admin.StackedInline):
    model = Room
    extra = 0
    can_delete = True
    fields = ("code", "max_capacity")
    show_change_link = False


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ("id", "username_display", "booking_date")
    search_fields = ("username__username",)
    list_filter = ("booking_date",)
    date_hierarchy = "booking_date"
    list_select_related = ("username",)
    autocomplete_fields = ("username",)
    readonly_fields = ("booking_date",)
    list_per_page = 50

    @admin.display(description="User", ordering="username")
    def username_display(self, obj):
        return getattr(obj.username, "username", "") or ""


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ("id", "type", "price", "code_display", "capacity_display")
    list_filter = ("type",)
    search_fields = ("id", "restaurant__code", "room__code")
    ordering = ("id",)
    list_select_related = ("restaurant", "room")
    actions = ("mark_available", "mark_occupied", "mark_maintenance")
    inlines = [RestaurantInline, RoomInline]
    list_per_page = 50

    def get_inline_instances(self, request, obj=None):
        instances = super().get_inline_instances(request, obj)
        if obj is None:
            return instances
        filtered = []
        for inline in instances:
            if isinstance(inline, RestaurantInline) and obj.type == "RESTAURANT":
                filtered.append(inline)
            elif isinstance(inline, RoomInline) and obj.type == "ROOM":
                filtered.append(inline)
        return filtered

    @admin.display(description="Code")
    def code_display(self, obj):
        return (
            getattr(getattr(obj, "room", None), "code", None)
            or getattr(getattr(obj, "restaurant", None), "code", None)
            or ""
        )

    @admin.display(description="Capacity")
    def capacity_display(self, obj):
        return (
            getattr(getattr(obj, "room", None), "max_capacity", None)
            or getattr(getattr(obj, "restaurant", None), "max_capacity", None)
            or ""
        )

    def mark_available(self, request, queryset):
        updated = queryset.update(status="AVAILABLE")
        self.message_user(request, f"{updated} services set to AVAILABLE.")

    mark_available.short_description = "Set status to AVAILABLE"

    def mark_occupied(self, request, queryset):
        updated = queryset.update(status="OCCUPIED")
        self.message_user(request, f"{updated} services set to OCCUPIED.")

    mark_occupied.short_description = "Set status to OCCUPIED"

    def mark_maintenance(self, request, queryset):
        updated = queryset.update(status="MAINTENANCE")
        self.message_user(request, f"{updated} services set to MAINTENANCE.")

    mark_maintenance.short_description = "Set status to MAINTENANCE"


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ("service", "code", "max_capacity")
    search_fields = ("code",)
    list_select_related = ("service",)


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ("service", "code", "max_capacity")
    search_fields = ("code",)
    list_select_related = ("service",)
