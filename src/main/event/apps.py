"""Django application configuration for the Event app.

This module declares the app config used by Django to register the
`event` application.
"""

from django.apps import AppConfig


class EventConfig(AppConfig):
    """AppConfig for the Event app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "event"
