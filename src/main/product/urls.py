"""URL patterns for the Product app.

Routes:
- GET  /products/          -> product catalog with optional search
- GET  /cart/              -> current user's shopping cart
- POST /cart/add/          -> add a product/qty to cart
- POST /cart/update/       -> update quantities in cart
- POST /cart/remove/       -> remove a product from cart
- POST /cart/checkout/     -> create order and order details (auth)
"""

from django.urls import path
from .views import (
    product_view,
    cart_view,
    add_to_cart,
    update_cart,
    remove_from_cart,
    checkout,
)

urlpatterns = [
    path("products/", product_view, name="product_list"),
    path("cart/", cart_view, name="cart"),
    path("cart/add/", add_to_cart, name="add_to_cart"),
    path("cart/update/", update_cart, name="update_cart"),
    path("cart/remove/", remove_from_cart, name="remove_from_cart"),
    path("cart/checkout/", checkout, name="checkout"),
]
