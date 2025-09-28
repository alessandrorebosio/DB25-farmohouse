"""
App configuration for the Review application.

This module declares the Django AppConfig for the `review` app.
"""

from django.apps import AppConfig


class ReviewConfig(AppConfig):
    """Django AppConfig for the `review` app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "review"
