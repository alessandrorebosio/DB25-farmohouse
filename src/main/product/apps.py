"""Django application configuration for the Product app.

Registers the `product` application with Django.
"""

from django.apps import AppConfig


class ProductConfig(AppConfig):
    """AppConfig for the Product app."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "product"
