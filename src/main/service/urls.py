from django.urls import path
from .views import *

app_name = 'service' 

urlpatterns = [
    path("services/", service_list, name="service_list"),
    path("<str:service_type>/book/", service_type_booking, name="service_type_booking"),
    path("results/", booking_results, name="booking_results"),
    path("confirm/<int:service_id>/", booking_confirm, name="booking_confirm"),
]