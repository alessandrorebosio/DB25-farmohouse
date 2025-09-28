"""Database models for user-generated reviews.

The `Review` table stores ratings and optional comments either for a Service or
an Event. Exactly one of `service` or `event` should be set per row. This app
maps existing database tables (managed = False).
"""

from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from user.models import User
from service.models import Service
from event.models import Event


class Review(models.Model):
    """A user's review for a service or an event.

    Schema (MySQL):
        CREATE TABLE REVIEW (
            id INT AUTO_INCREMENT PRIMARY KEY,
            `user` VARCHAR(255) NOT NULL,        -- FK to users_user.username
            service INT NULL,                    -- FK to service table
            event INT NULL,                      -- FK to event table
            rating SMALLINT NOT NULL CHECK (rating BETWEEN 1 AND 5),
            comment TEXT NULL,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE KEY uq_user_service (`user`, service),
            UNIQUE KEY uq_user_event (`user`, event)
        );

    Notes:
    - Exactly one of `service` or `event` should be non-null.
    - `managed=False` because the table already exists and is not managed by Django.
    """

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
        verbose_name = "Review"
        verbose_name_plural = "Reviews"

    def __str__(self) -> str:
        target = self.service or self.event
        target_label = getattr(target, "title", None) or str(target) if target else "-"
        return f"Review(id={self.id}, user={self.user_id}, rating={self.rating}, target={target_label})"
