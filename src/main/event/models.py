# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models
from users.models import User, Employee


class Event(models.Model):
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


class EventSubscription(models.Model):
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
