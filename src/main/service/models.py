from django.db import models


class Reservation(models.Model):
    id = models.AutoField(primary_key=True)
    username = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        db_column="username",
        to_field="username",
        related_name="reservations",
    )
    reservation_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = "RESERVATION"


class Service(models.Model):
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
    status = models.CharField(
        max_length=20,
        choices=[
            ("AVAILABLE", "Available"),
            ("OCCUPIED", "Occupied"),
            ("MAINTENANCE", "Maintenance"),
        ],
        default="AVAILABLE",
    )

    class Meta:
        managed = False
        db_table = "SERVICE"


class ReservationDetail(models.Model):
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

    class Meta:
        managed = False
        db_table = "RESERVATION_DETAIL"
        unique_together = (("reservation", "service"),)


class Restaurant(models.Model):
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


class Room(models.Model):
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
