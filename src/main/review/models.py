from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from users.models import User
from service.models import Service
from event.models import Event

# Create your models here.
class Review(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        db_column="user",
        to_field="username",
        related_name="reviews",
    )
    service = models.ForeignKey(
        Service,
        on_delete=models.CASCADE,
        db_column="service",
        blank=True,
        null=True,
        related_name="reviews",
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        db_column="event",
        blank=True,
        null=True,
        related_name="reviews",
    )
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, db_column="created_at")

    class Meta:
        managed = False
        db_table = "REVIEW"
        unique_together = (
            ("user", "service"),
            ("user", "event"),
        )
