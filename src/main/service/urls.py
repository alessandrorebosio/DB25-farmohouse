from django.urls import path
from . import views

app_name = "service"

urlpatterns = [
    path("services/", views.service_list, name="service_list"),
    path("book/<int:service_id>/quick/", views.quick_book, name="quick_book"),
    path(
        "booking/<int:service_id>/confirm/",
        views.booking_confirm,
        name="booking_confirm",
    ),
]
