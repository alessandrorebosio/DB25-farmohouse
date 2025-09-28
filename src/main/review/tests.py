"""Lightweight tests for the review app.

These tests avoid relying on unmanaged DB tables. They only test routing and
authentication guards (redirects for anonymous users).
"""

from django.test import TestCase
from django.urls import reverse, resolve
from django.contrib.auth import get_user_model


class ReviewUrlsTest(TestCase):
    def test_routes_resolve(self):
        self.assertEqual(resolve(reverse("review_list")).url_name, "review_list")

        self.assertEqual(
            resolve(reverse("event_review", kwargs={"event_id": 1})).url_name,
            "event_review",
        )
        self.assertEqual(
            resolve(reverse("service_review", kwargs={"service_id": 1})).url_name,
            "service_review",
        )


class ReviewAuthGuardsTest(TestCase):
    def test_event_review_requires_login(self):
        resp = self.client.get(reverse("event_review", kwargs={"event_id": 999}))
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login", resp.headers.get("Location", ""))

    def test_service_review_requires_login(self):
        resp = self.client.get(reverse("service_review", kwargs={"service_id": 999}))
        self.assertEqual(resp.status_code, 302)
        self.assertIn("/login", resp.headers.get("Location", ""))
