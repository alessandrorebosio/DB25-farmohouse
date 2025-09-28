"""URL patterns for the Event app.

Routes:
- GET /events/                      -> events list page (upcoming, searchable)
- POST /events/<id>/book/           -> book N participants for an event (auth)
- POST /events/<id>/cancel/         -> cancel current user's booking (auth)
"""

from django.urls import path

from . import views

urlpatterns = [
    path("events/", views.event_view, name="event_list"),
    path("events/<int:event_id>/book/", views.book_event, name="event_book"),
    path("events/<int:event_id>/cancel/", views.cancel_event, name="event_cancel"),
]
