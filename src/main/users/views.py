from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse
from django.db.models import F, Sum, DecimalField, Prefetch, ExpressionWrapper

from .forms import RegisterForm
from . import models
from product.models import Orders, OrderDetail


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
        return render(request, "profile.html", {"query": None, "orders": []})

    query = {
        "employee": getattr(ut, "employee", None),
        "person": getattr(ut, "cf", None),
    }

    # Ordini dell’utente con righe e totali
    line_qs = (
        OrderDetail.objects.select_related("product")
        .annotate(
            line_total=ExpressionWrapper(
                F("quantity") * F("unit_price"),
                output_field=DecimalField(max_digits=12, decimal_places=2),
            )
        )
        .order_by("product__name")
    )

    orders = (
        Orders.objects.filter(username_id=request.user.username)
        .annotate(
            order_total=Sum(
                ExpressionWrapper(
                    F("orderdetail__quantity") * F("orderdetail__unit_price"),
                    output_field=DecimalField(max_digits=12, decimal_places=2),
                )
            )
        )
        .prefetch_related(
            Prefetch("orderdetail_set", queryset=line_qs, to_attr="lines")
        )
        .order_by("-date", "-id")
    )

    return render(
        request,
        "profile.html",
        {"query": query, "orders": orders},
    )


def logout_view(request: HttpRequest) -> HttpResponse:
    logout(request)
    return render(request, "index.html")
