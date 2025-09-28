"""Database models for the Event app.

Note: These models map to existing tables (managed=False). We only add
docstrings and user-friendly __str__ methods to improve readability and
admin display without altering the database schema.
"""

from django.db import models
from users.models import User, Employee


class Event(models.Model):
    """Represents an event with a title, date, seats and creator."""

    seats = models.IntegerField()
    title = models.CharField(max_length=100)
    description = models.TextField()
    event_date = models.DateField()
    created_by = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        db_column="created_by",
        to_field="username",
        related_name="events_created",
    )

    class Meta:
        managed = False
        db_table = "EVENT"
        verbose_name = "Event"
        verbose_name_plural = "Events"

    def __str__(self) -> str:
        """Human-friendly representation used in admin and logs."""
        return f"{self.title} ({self.event_date:%Y-%m-%d})"


class EventSubscription(models.Model):
    """A user's subscription to an event, with participant count."""

    pk = models.CompositePrimaryKey("event", "user")
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        db_column="event",
        related_name="subscriptions",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        db_column="user",
        to_field="username",
        related_name="event_subscriptions",
    )
    subscription_date = models.DateTimeField(blank=True, null=True)
    participants = models.IntegerField()

    class Meta:
        managed = False
        db_table = "EVENT_SUBSCRIPTION"
        verbose_name = "Event subscription"
        verbose_name_plural = "Event subscriptions"

    def __str__(self) -> str:
        """Readable summary: username -> event (N participants)."""
        uname = getattr(self.user, "username", "?")
        return f"{uname} -> {self.event} ({self.participants} participants)"
