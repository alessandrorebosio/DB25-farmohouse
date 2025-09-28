"""URL routes for the Service app.

Routes:
- /services/ → Browse available services with filters
- /book/<id>/quick/ → Quick booking flow (auth required)
- /cancel-reservation/<id>/ → Cancel reservation (auth + POST required)
"""

from django.urls import path
from . import views

app_name = "service"

urlpatterns = [
    path("services/", views.service_list, name="service_list"),
    path("book/<int:service_id>/quick/", views.quick_book, name="quick_book"),
    path(
        "cancel-reservation/<int:reservation_id>/",
        views.cancel_reservation,
        name="cancel_reservation",
    ),
]
