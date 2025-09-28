# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
"""Database models for the Product app.

These models point to existing tables (managed=False). The added docstrings
and __str__ methods improve admin readability without altering the schema.
"""

from django.db import models


# Create your models here.
class Orders(models.Model):
    """A customer order with a creation date and username (to_field)."""

    date = models.DateTimeField(blank=True, null=True)
    username = models.ForeignKey(
        "users.User",
        on_delete=models.CASCADE,
        db_column="username",
        to_field="username",
        related_name="orders",
    )

    class Meta:
        managed = False
        db_table = "ORDERS"
        verbose_name = "Order"
        verbose_name_plural = "Orders"

    def __str__(self) -> str:
        return f"Order #{getattr(self, 'id', '?')} by {getattr(self.username, 'username', '?')}"


class OrderDetail(models.Model):
    """An order line for a given product with quantity and unit price."""

    pk = models.CompositePrimaryKey("order", "product")
    order = models.ForeignKey(Orders, models.CASCADE, db_column="order")
    product = models.ForeignKey("Product", models.CASCADE, db_column="product")
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        managed = False
        db_table = "ORDER_DETAIL"
        verbose_name = "Order detail"
        verbose_name_plural = "Order details"

    def __str__(self) -> str:
        return f"OrderDetail(order={getattr(self.order, 'id', '?')}, product={getattr(self.product, 'id', '?')})"


class Product(models.Model):
    """A product with name, description and price."""

    name = models.CharField(max_length=100)
    description = models.TextField()  # added
    price = models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        managed = False
        db_table = "PRODUCT"
        verbose_name = "Product"
        verbose_name_plural = "Products"

    def __str__(self) -> str:
        return f"{self.name} ({self.price})"
