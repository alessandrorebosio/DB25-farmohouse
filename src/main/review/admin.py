"""Admin configuration for Review.

This module registers the `Review` model in Django admin with a custom form
that ensures exactly one between `service` and `event` is set.
"""

from django.contrib import admin
from django import forms
from .models import Review


class ReviewAdminForm(forms.ModelForm):
    """Admin form validating that one and only one target is selected.

    Constraints:
    - Either `service` or `event` must be provided (exclusively).
    """

    class Meta:
        model = Review
        fields = "__all__"

    def clean(self):
        cleaned = super().clean()
        service = cleaned.get("service")
        event = cleaned.get("event")
        # Exactly one between service and event
        if bool(service) == bool(event):
            raise forms.ValidationError("Set either service or event (exactly one).")
        return cleaned


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    form = ReviewAdminForm

    readonly_fields = ("created_at",)
    raw_id_fields = ("user", "service", "event")
    list_display = ("id", "user", "target_type", "target_label", "rating", "created_at")
    list_filter = (
        "rating",
        ("created_at", admin.DateFieldListFilter),
        "service",
        "event",
    )
    search_fields = ("user__username", "comment", "event__title")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)
    list_select_related = ("user", "service", "event")
    list_per_page = 50

    fieldsets = (
        (None, {"fields": ("user", "rating", "comment")}),
        (
            "Target",
            {
                "fields": ("service", "event"),
                "description": "Fill exactly one between service and event.",
            },
        ),
        ("Meta", {"fields": ("created_at",)}),
    )

    @admin.display(description="Target type")
    def target_type(self, obj):
        return "SERVICE" if obj.service_id else "EVENT"

    @admin.display(description="Target")
    def target_label(self, obj):
        if obj.service_id:
            return str(obj.service) if obj.service_id else "-"
        return obj.event.title if obj.event_id else "-"
