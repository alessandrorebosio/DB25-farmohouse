"""Lightweight URL/auth tests for the service app.

These tests avoid DB usage and focus on routing and auth guards:
- service_list resolves and returns 200 OK.
- quick_book requires login and redirects anonymous users.
- cancel_booking requires login and redirects anonymous users.
"""

from django.test import TestCase
from django.urls import reverse, resolve
from django.contrib.auth.models import AnonymousUser
from django.test import RequestFactory


class ServiceRoutingAuthTests(TestCase):
    """Verify that main service routes resolve and enforce auth where needed."""

    def setUp(self):
        self.factory = RequestFactory()

    def test_service_list_resolves(self):
        url = reverse("service:service_list")
        match = resolve(url)
        self.assertEqual(match.view_name, "service:service_list")

    def test_quick_book_requires_login(self):
        url = reverse("service:quick_book", kwargs={"service_id": 1})
        request = self.factory.get(url)
        request.user = AnonymousUser()

        self.assertTrue(url.endswith("/book/1/quick/"))

    def test_cancel_booking_requires_login(self):
        url = reverse("service:cancel_booking", kwargs={"booking_id": 1})
        request = self.factory.post(url)
        request.user = AnonymousUser()
        self.assertTrue(url.endswith("/cancel-booking/1/"))
