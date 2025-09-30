"""Unmanaged models mapping existing Service-related tables.

Tables:
- SERVICE, RESTAURANT, ROOM, BOOKING, BOOKING_DETAIL
"""

from django.db import models
from django.core.validators import MinValueValidator
from user.models import User


class Booking(models.Model):
    """A booking container for a user.

    Maps to BOOKING(id, username, booking_date).
    """

    id = models.AutoField(primary_key=True)
    username = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        db_column="username",
        to_field="username",
        related_name="bookings",
    )
    booking_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = "BOOKING"
        verbose_name = "Booking"
        verbose_name_plural = "Bookings"

    def __str__(self) -> str:
        return f"Booking(id={self.id}, user={self.username_id})"


class Service(models.Model):
    """A service that can be reserved (Room, Restaurant, etc.)."""

    id = models.AutoField(primary_key=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    type = models.CharField(
        max_length=20,
        choices=[
            ("RESTAURANT", "Restaurant"),
            ("ROOM", "Room"),
        ],
    )

    class Meta:
        managed = False
        db_table = "SERVICE"
        verbose_name = "Service"
        verbose_name_plural = "Services"

    def __str__(self) -> str:
        return f"Service(id={self.id}, type={self.type})"


class BookingDetail(models.Model):
    """Join table for bookings and services with time bounds."""

    pk = models.CompositePrimaryKey("booking", "service")
    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        db_column="booking",
        related_name="details",
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        db_column="service",
        related_name="BOOKING_DETAILs",
    )
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    people = models.IntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(
        max_digits=8, decimal_places=2, validators=[MinValueValidator(0)]
    )

    class Meta:
        managed = False
        db_table = "BOOKING_DETAIL"
        unique_together = (("booking", "service"),)
        verbose_name = "Booking detail"
        verbose_name_plural = "Booking details"

    def __str__(self) -> str:
        return f"BookingDetail(booking={self.booking_id}, service={self.service_id})"


class Restaurant(models.Model):
    """Restaurant-specific properties for a Service."""

    service = models.OneToOneField(
        Service,
        on_delete=models.CASCADE,
        db_column="service",
        primary_key=True,
        related_name="restaurant",
    )
    code = models.CharField(max_length=3, unique=True)
    max_capacity = models.IntegerField()

    class Meta:
        managed = False
        db_table = "RESTAURANT"
        verbose_name = "Restaurant"
        verbose_name_plural = "Restaurants"

    def __str__(self) -> str:
        return f"Restaurant(service={self.service_id}, code={self.code})"


class Room(models.Model):
    """Room-specific properties for a Service."""

    service = models.OneToOneField(
        Service,
        on_delete=models.CASCADE,
        db_column="service",
        primary_key=True,
        related_name="room",
    )
    code = models.CharField(max_length=3, unique=True)
    max_capacity = models.IntegerField()

    class Meta:
        managed = False
        db_table = "ROOM"
        verbose_name = "Room"
        verbose_name_plural = "Rooms"

    def __str__(self) -> str:
        return f"Room(service={self.service_id}, code={self.code})"
