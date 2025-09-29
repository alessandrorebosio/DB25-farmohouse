"""URL patterns for the User app.

Routes: register, login, logout, profile and staff statistics, aligned with
the concise documentation style used in the Event app.
"""

from django.urls import path

from . import views

urlpatterns = [
    path("register/", views.register_view, name="register"),
    path("login/", views.login_view, name="login"),
    path("profile/", views.profile_view, name="profile"),
    path("statistic/", views.statistic_view, name="statistic"),
    path("logout/", views.logout_view, name="logout"),
]
