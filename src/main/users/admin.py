from django import forms
from django.contrib import admin
from django.contrib.auth.hashers import make_password

from . import models


class EmployeeHistoryInline(admin.TabularInline):
    model = models.EmployeeHistory
    extra = 0
    can_delete = False
    readonly_fields = ("fired_at",)
    fields = ("fired_at",)
    show_change_link = False


class EmployeeShiftInline(admin.TabularInline):
    model = models.EmployeeShift
    extra = 0
    readonly_fields = ("shift_date", "shift")
    fields = ("shift_date", "shift")
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

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if "password" in form.base_fields:
            form.base_fields["password"].widget = forms.PasswordInput(render_value=True)
            if obj:
                form.base_fields["password"].help_text = (
                    "Leave blank to keep current password."
                )
                form.base_fields["password"].required = False
            else:
                form.base_fields["password"].help_text = "Enter a new password."
        return form

    def save_model(self, request, obj, form, change):
        raw = form.cleaned_data.get("password")
        if change and not raw:
            old = type(obj).objects.get(pk=obj.pk)
            obj.password = old.password
        else:
            if raw and not raw.startswith(("pbkdf2_", "argon2$", "bcrypt$")):
                obj.password = make_password(raw)
        super().save_model(request, obj, form, change)


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
    list_display = ("username", "fired_at")
    search_fields = ("username__username",)
    list_filter = ("fired_at",)
    date_hierarchy = "fired_at"
    ordering = ("-fired_at",)
    list_select_related = ("username",)


@admin.register(models.EmployeeShift)
class EmployeeShiftAdmin(admin.ModelAdmin):
    list_display = ("employee_username", "shift_date", "shift")
    search_fields = ("employee_username__username", "shift__shift_name")
    list_filter = ("shift_date", "shift__shift_name")
    ordering = ("-shift_date",)
    list_select_related = ("employee_username", "shift")
    autocomplete_fields = ("employee_username", "shift")


@admin.register(models.Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = ("shift_name", "day", "start_time", "end_time")
    search_fields = ("shift_name", "day")
    list_filter = ("day",)
    ordering = ("day", "start_time")


@admin.register(models.ActiveEmployee)
class ActiveEmployeeAdmin(admin.ModelAdmin):
    list_display = ("username", "role")
    search_fields = ("username", "role")
    ordering = ("username",)
    readonly_fields = ("username", "role")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
