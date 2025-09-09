from django.contrib import admin
from . import models


class EmployeeHistoryInline(admin.TabularInline):
    model = models.EmployeeHistory
    extra = 0
    can_delete = False
    readonly_fields = ("role", "change_date")
    fields = ("role", "change_date")
    show_change_link = False


class EmployeeShiftInline(admin.TabularInline):
    model = models.EmployeeShift
    extra = 0
    readonly_fields = ("shift_date", "shift", "status")
    fields = ("shift_date", "shift", "status")
    show_change_link = True
    autocomplete_fields = ("shift",)


@admin.register(models.Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ("cf", "name", "surname")
    search_fields = ("cf", "name", "surname")
    ordering = ("surname", "name")


@admin.register(models.User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("username", "email", "cf")
    search_fields = ("username", "email", "cf__cf", "cf__name", "cf__surname")
    list_select_related = ("cf",)
    ordering = ("username",)


@admin.register(models.Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("username_id", "role")
    search_fields = (
        "username__username",
        "username__email",
        "username__cf__name",
        "username__cf__surname",
    )
    list_select_related = ("username",)
    inlines = [EmployeeHistoryInline, EmployeeShiftInline]
    ordering = ("username_id",)
    autocomplete_fields = ("username",)


@admin.register(models.EmployeeHistory)
class EmployeeHistoryAdmin(admin.ModelAdmin):
    list_display = ("username", "role", "change_date")
    search_fields = ("username__username", "role")
    list_filter = ("role", "change_date")
    date_hierarchy = "change_date"
    ordering = ("-change_date",)
    list_select_related = ("username",)


@admin.register(models.EmployeeShift)
class EmployeeShiftAdmin(admin.ModelAdmin):
    list_display = ("employee_username", "shift_date", "shift", "status")
    search_fields = ("employee_username__username", "shift__shift_name")
    list_filter = ("status", "shift_date", "shift__shift_name")
    ordering = ("-shift_date",)
    list_select_related = ("employee_username", "shift")
    autocomplete_fields = ("employee_username", "shift")


@admin.register(models.Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ("shift_name", "day", "start_time", "end_time")
    search_fields = ("shift_name", "day")
    list_filter = ("day",)
    ordering = ("day", "start_time")
