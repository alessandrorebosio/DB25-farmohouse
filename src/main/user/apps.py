"""App configuration for the User app.

Keeps Django default settings and declares the app label and name.
Documented to align with the style used in other apps (e.g., Event).
"""

from django.apps import AppConfig


class UserConfig(AppConfig):
    """Django AppConfig for the `user` app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "user"
