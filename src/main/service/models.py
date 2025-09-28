"""Unmanaged models mapping existing Service-related tables.

Tables:
- SERVICE, RESTAURANT, ROOM, RESERVATION, RESERVATION_DETAIL
"""

from django.db import models
from user.models import User

class Reservation(models.Model):
    """A booking container for a user.

    Schema (MySQL):
        CREATE TABLE RESERVATION (
            id INT AUTO_INCREMENT PRIMARY KEY,
            `username` VARCHAR(255) NOT NULL,
            reservation_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
    """

    id = models.AutoField(primary_key=True)
    username = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        db_column="username",
        to_field="username",
        related_name="reservations",
    )
    reservation_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = "RESERVATION"
        verbose_name = "Reservation"
        verbose_name_plural = "Reservations"

    def __str__(self) -> str:
        return f"Reservation(id={self.id}, user={self.username_id})"


class Service(models.Model):
    """A service that can be reserved (Room, Restaurant, etc.)."""

    id = models.AutoField(primary_key=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    type = models.CharField(
        max_length=20,
        choices=[
            ("RESTAURANT", "Restaurant"),
            ("POOL", "Pool"),
            ("PLAYGROUND", "Playground"),
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


class ReservationDetail(models.Model):
    """Join table for reservations and services with time bounds."""

    pk = models.CompositePrimaryKey("reservation", "service")
    reservation = models.ForeignKey(
        Reservation,
        on_delete=models.CASCADE,
        db_column="reservation",
        related_name="details",
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        db_column="service",
        related_name="reservation_details",
    )
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    people = models.IntegerField()

    class Meta:
        managed = False
        db_table = "RESERVATION_DETAIL"
        unique_together = (("reservation", "service"),)
        verbose_name = "Reservation detail"
        verbose_name_plural = "Reservation details"

    def __str__(self) -> str:
        return (
            f"ReservationDetail(res={self.reservation_id}, service={self.service_id})"
        )


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
