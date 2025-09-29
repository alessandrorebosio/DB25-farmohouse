"""Models for the User app.

Important notes:
- All models map to existing database tables/views (managed = False)
- Primary keys reflect the legacy schema as-is
- Field and table names (db_table/db_column) are kept for compatibility

This file mirrors the explanatory style used in Event app code, adding
clear docstrings for maintenance without changing behavior.
"""

from django.db import models


class ActiveEmployee(models.Model):
    """Read-only projection for active employees with their role.

    Backed by the "active_employees" table or view. Used to determine
    staff/superuser in the custom auth backend.
    """

    username = models.CharField(primary_key=True, max_length=32)
    role = models.CharField(max_length=32)

    class Meta:
        managed = False
        db_table = "active_employees"
        verbose_name = "Active employee"
        verbose_name_plural = "Active employees"


class FullyBookedEvent(models.Model):
    """Materialized view of fully booked events (reporting convenience).

    Provides quick access to events that have no remaining seats.
    """

    id = models.IntegerField(primary_key=True, db_column="id")
    title = models.CharField(max_length=255, null=True, db_column="title")
    event_date = models.TimeField(null=True, db_column="event_date")
    seats = models.IntegerField(null=True, db_column="seats")
    total_participants = models.IntegerField(null=True, db_column="total_participants")

    class Meta:
        managed = False
        db_table = "fully_booked_events"
        ordering = ["-event_date"]


class FreeServiceNow(models.Model):
    """Projection of services with their current availability state."""

    service_id = models.IntegerField(primary_key=True, db_column="service_id")
    type = models.CharField(max_length=50, null=True, db_column="type")
    restaurant_code = models.CharField(
        max_length=64, null=True, db_column="restaurant_code"
    )
    room_code = models.CharField(max_length=64, null=True, db_column="room_code")
    restaurant_max_capacity = models.IntegerField(
        null=True, db_column="restaurant_max_capacity"
    )
    room_max_capacity = models.IntegerField(null=True, db_column="room_max_capacity")
    people_booked_now = models.IntegerField(null=True, db_column="people_booked_now")
    reservations_now = models.IntegerField(null=True, db_column="reservations_now")
    available = models.BooleanField(null=True, db_column="available")
    available_seats = models.IntegerField(null=True, db_column="available_seats")

    class Meta:
        managed = False
        db_table = "free_services_now"


class Employee(models.Model):
    """Employee entity linked 1:1 to the application User by username."""

    username = models.OneToOneField(
        "User", models.CASCADE, db_column="username", primary_key=True
    )
    role = models.CharField(max_length=32)

    class Meta:
        managed = False
        db_table = "EMPLOYEE"
        verbose_name = "Employee"
        verbose_name_plural = "Employees"


class EmployeeHistory(models.Model):
    """Employment history entries; one row per fired event per employee."""

    username = models.ForeignKey(Employee, models.CASCADE, db_column="username")
    fired_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "EMPLOYEE_HISTORY"
        verbose_name = "Employee history"
        verbose_name_plural = "Employee histories"


class EmployeeShift(models.Model):
    """Assignment of an employee to a shift on a specific date.

    unique_together ensures one shift per employee per date.
    """

    employee_username = models.ForeignKey(
        Employee, models.CASCADE, db_column="employee_username"
    )
    shift = models.ForeignKey("Shift", models.CASCADE)
    shift_date = models.DateField()

    class Meta:
        managed = False
        db_table = "EMPLOYEE_SHIFT"
        unique_together = (("employee_username", "shift_date"),)
        verbose_name = "Employee shift"
        verbose_name_plural = "Employee shifts"


class Person(models.Model):
    """Personal identity information (CF as primary key)."""

    cf = models.CharField(primary_key=True, max_length=16)
    name = models.CharField(max_length=32)
    surname = models.CharField(max_length=32)

    class Meta:
        managed = False
        db_table = "PERSON"
        verbose_name = "Person"
        verbose_name_plural = "People"


class Shift(models.Model):
    """Shift catalog: logical name, day and time bounds."""

    day = models.CharField(max_length=3)
    shift_name = models.CharField(max_length=32)
    start_time = models.TimeField()
    end_time = models.TimeField()

    class Meta:
        managed = False
        db_table = "SHIFT"
        verbose_name = "Shift"
        verbose_name_plural = "Shifts"


class User(models.Model):
    """Application-level user account linked to a Person.

    This is separate from Django's auth user; the custom backend bridges
    between the two.
    """

    cf = models.OneToOneField(Person, models.CASCADE, db_column="cf")
    username = models.CharField(primary_key=True, max_length=32)
    email = models.CharField(max_length=255)
    password = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = "USER"
        verbose_name = "User"
        verbose_name_plural = "Users"
