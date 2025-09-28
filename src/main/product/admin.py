"""Admin configuration for the Product app.

Adds computed totals for orders, read-only inline for order details, and
query optimizations to avoid N+1 problems. Includes English docstrings.
"""

from django.contrib import admin
from django.db.models import Sum, F, DecimalField
from django.db.models.functions import Coalesce
from . import models


class OrderDetailInline(admin.TabularInline):
    """Read-only inline displaying the order lines for an order."""

    model = models.OrderDetail
    extra = 0
    autocomplete_fields = ("product",)
    readonly_fields = ("product", "quantity", "unit_price", "line_total")
    fields = ("product", "quantity", "unit_price", "line_total")
    can_delete = False

    def line_total(self, obj):
        return (obj.quantity or 0) * (obj.unit_price or 0)

    line_total.short_description = "Line total"


@admin.register(models.Orders)
class OrdersAdmin(admin.ModelAdmin):
    list_display = ("id", "username_id", "date", "total_items", "total_amount")
    search_fields = ("id", "username__username")
    list_filter = ("date",)
    date_hierarchy = "date"
    inlines = [OrderDetailInline]
    ordering = ("-date",)
    readonly_fields = ("date", "username")
    list_select_related = ("username",)

    def get_queryset(self, request):
        qs = super().get_queryset(request).select_related("username")
        return qs.annotate(
            _items=Coalesce(Sum("orderdetail__quantity"), 0),
            _amount=Coalesce(
                Sum(F("orderdetail__quantity") * F("orderdetail__unit_price")),
                0,
                output_field=DecimalField(max_digits=12, decimal_places=2),
            ),
        )

    @admin.display(description="Items", ordering="_items")
    def total_items(self, obj):
        return obj._items

    @admin.display(description="Amount", ordering="_amount")
    def total_amount(self, obj):
        return obj._amount


@admin.register(models.Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "price", "ordered_qty", "short_description")
    search_fields = ("name", "description")
    ordering = ("name",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(_ordered=Coalesce(Sum("orderdetail__quantity"), 0))

    @admin.display(description="Ordered Qty", ordering="_ordered")
    def ordered_qty(self, obj):
        return obj._ordered

    def short_description(self, obj):
        if not obj.description:
            return ""
        text = str(obj.description)
        return text if len(text) <= 80 else text[:80] + "…"

    short_description.short_description = "Description"
