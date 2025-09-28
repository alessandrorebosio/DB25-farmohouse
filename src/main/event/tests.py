"""Unit tests for the Event app.

These tests focus on routing, authentication requirements, and basic
view contract checks that don't rely on database migrations. Where DB
interaction is necessary, tests are marked to safely skip if the
underlying tables are unmanaged or missing.
"""

from django.test import TestCase
from django.urls import reverse, resolve
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
from django.test.client import RequestFactory
from django.utils import timezone
from unittest import skipIf
from django.db import connection

from . import views


def _table_exists(name: str) -> bool:
    """Return True if a database table with the given name exists."""
    with connection.cursor() as cur:
        tables = connection.introspection.table_names(cursor=cur)
    return name in tables


class UrlsTests(TestCase):
    """Smoke tests for URL routing names and view callables."""

    def test_event_list_url(self):
        url = reverse("event_list")
        self.assertEqual(url, "/events/")
        match = resolve(url)
        self.assertIs(match.func, views.event_view)

    def test_event_book_url(self):
        url = reverse("event_book", args=[123])
        self.assertEqual(url, "/events/123/book/")
        match = resolve(url)
        self.assertIs(match.func, views.book_event)

    def test_event_cancel_url(self):
        url = reverse("event_cancel", args=[123])
        self.assertEqual(url, "/events/123/cancel/")
        match = resolve(url)
        self.assertIs(match.func, views.cancel_event)


class EventListViewTests(TestCase):
    """Tests for the event list view behavior that don't require DB state."""

    def setUp(self):
        self.factory = RequestFactory()

    def test_event_list_renders_template(self):

        req = self.factory.get("/events/")
        req.user = AnonymousUser()
        resp = views.event_view(req)
        self.assertEqual(resp.status_code, 200)

        self.assertIn(b"Events", resp.content)


@skipIf(
    not (_table_exists("EVENT") and _table_exists("EVENT_SUBSCRIPTION")),
    "Database tables for Event app are unmanaged or missing.",
)
class BookingFlowTests(TestCase):
    """DB-backed tests that exercise booking/cancellation endpoints.

    Skipped automatically if the required tables are not present.
    """

    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(username="alice", password="pwd")

    def test_booking_requires_auth(self):
        url = reverse("event_book", args=[1])
        resp = self.client.post(url, {"participants": 1})

        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login", resp.url)

    def test_cancel_requires_auth(self):
        url = reverse("event_cancel", args=[1])
        resp = self.client.post(url)
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login", resp.url)
