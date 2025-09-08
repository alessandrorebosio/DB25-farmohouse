from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse


from .forms import RegisterForm
from . import models


# Create your views here.
def register_view(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("login")
    else:
        form = RegisterForm()

    return render(request, "register.html", {"form": form})


def login_view(request: HttpRequest) -> HttpResponse:
    next_url = request.POST.get("next") or request.GET.get("next") or "/"
    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect(next_url)
    else:
        form = AuthenticationForm(request)

    return render(request, "login.html", {"form": form, "next": next_url})


@login_required(login_url="login")
def profile_view(request: HttpRequest) -> HttpResponse:
    try:
        ut = models.User.objects.select_related("cf", "employee").get(
            username=request.user.username
        )
    except models.User.DoesNotExist:
        return render(request, "profile.html", {"query": None})

    query = {
        "employee": getattr(ut, "employee", None),
        "person": getattr(ut, "cf", None),
    }

    return render(
        request,
        "profile.html",
        {"query": query},
    )


def logout_view(request: HttpRequest) -> HttpResponse:
    logout(request)
    return render(request, "index.html")
