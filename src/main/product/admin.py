from django.contrib import admin
from django.db.models import Sum, F, DecimalField
from . import models


class OrderDetailInline(admin.TabularInline):
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

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(
            _items=Sum("orderdetail__quantity"),
            _amount=Sum(
                F("orderdetail__quantity") * F("orderdetail__unit_price"),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            ),
        )

    def total_items(self, obj):
        return obj._items or 0

    total_items.short_description = "Items"

    def total_amount(self, obj):
        return obj._amount or 0

    total_amount.short_description = "Amount"
    total_amount.admin_order_field = "_amount"


@admin.register(models.Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "price", "ordered_qty", "short_description")
    search_fields = ("name", "description")
    ordering = ("name",)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.annotate(_ordered=Sum("orderdetail__quantity"))

    def ordered_qty(self, obj):
        return obj._ordered or 0

    ordered_qty.short_description = "Ordered Qty"

    def short_description(self, obj):
        if not obj.description:
            return ""
        text = str(obj.description)
        return text if len(text) <= 80 else text[:80] + "…"

    short_description.short_description = "Description"
