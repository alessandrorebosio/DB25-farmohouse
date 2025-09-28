# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class ActiveEmployee(models.Model):
    username = models.CharField(primary_key=True, max_length=32)
    role = models.CharField(max_length=32)

    class Meta:
        managed = False
        db_table = "active_employees"
        verbose_name = "Active employee"
        verbose_name_plural = "Active employees"

class FullyBookedEvent(models.Model):
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
    service_id = models.IntegerField(primary_key=True, db_column="service_id")
    type = models.CharField(max_length=50, null=True, db_column="type")
    restaurant_code = models.CharField(max_length=64, null=True, db_column="restaurant_code")
    room_code = models.CharField(max_length=64, null=True, db_column="room_code")
    restaurant_max_capacity = models.IntegerField(null=True, db_column="restaurant_max_capacity")
    room_max_capacity = models.IntegerField(null=True, db_column="room_max_capacity")
    people_booked_now = models.IntegerField(null=True, db_column="people_booked_now")
    reservations_now = models.IntegerField(null=True, db_column="reservations_now")
    available = models.BooleanField(null=True, db_column="available")
    available_seats = models.IntegerField(null=True, db_column="available_seats")

    class Meta:
        managed = False
        db_table = "free_services_now"
        
class Employee(models.Model):
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
    username = models.ForeignKey(Employee, models.CASCADE, db_column="username")
    fired_at = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "EMPLOYEE_HISTORY"
        verbose_name = "Employee history"
        verbose_name_plural = "Employee histories"


class EmployeeShift(models.Model):
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
    cf = models.CharField(primary_key=True, max_length=16)
    name = models.CharField(max_length=32)
    surname = models.CharField(max_length=32)

    class Meta:
        managed = False
        db_table = "PERSON"
        verbose_name = "Person"
        verbose_name_plural = "People"


class Shift(models.Model):
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
    cf = models.OneToOneField(Person, models.CASCADE, db_column="cf")
    username = models.CharField(primary_key=True, max_length=32)
    email = models.CharField(max_length=255)
    password = models.CharField(max_length=255)

    class Meta:
        managed = False
        db_table = "USER"
        verbose_name = "User"
        verbose_name_plural = "Users"
