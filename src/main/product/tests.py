"""Unit tests for the Product app.

Lightweight tests verify URL routing and authentication requirements
without depending on unmanaged database tables.
"""

from django.test import TestCase
from django.urls import reverse, resolve
from django.contrib.auth import get_user_model

from . import views


class UrlsTests(TestCase):
    def test_product_list_url(self):
        url = reverse("product_list")
        self.assertEqual(url, "/products/")
        self.assertIs(resolve(url).func, views.product_view)

    def test_cart_urls(self):
        self.assertEqual(reverse("cart"), "/cart/")
        self.assertEqual(reverse("add_to_cart"), "/cart/add/")
        self.assertEqual(reverse("update_cart"), "/cart/update/")
        self.assertEqual(reverse("remove_from_cart"), "/cart/remove/")
        self.assertEqual(reverse("checkout"), "/cart/checkout/")


class AuthGuardTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="bob", password="pwd")

    def test_cart_requires_login(self):
        resp = self.client.get(reverse("cart"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login", resp.url)

    def test_checkout_requires_login(self):
        resp = self.client.post(reverse("checkout"))
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login", resp.url)
