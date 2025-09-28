"""URL routes for the Review app.

Routes:
- /reviews/ → List/filter all reviews
- /event/<id>/review/ → Create/update a review for an event (auth required)
- /service_review/<id>/ → Create/update a review for a service (auth required)
"""

from django.urls import path
from .views import review_view, event_review_view, service_review_view

urlpatterns = [
    path("reviews/", review_view, name="review_list"),
    path("event/<int:event_id>/review/", event_review_view, name="event_review"),
    path(
        "service_review/<int:service_id>/", service_review_view, name="service_review"
    ),
]
