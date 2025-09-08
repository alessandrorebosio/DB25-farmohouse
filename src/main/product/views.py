from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse, HttpResponseBadRequest
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.db import transaction, connection
from decimal import Decimal
from django.utils import timezone

from .models import Product, Orders


def _get_cart(session) -> dict:
    return session.setdefault("cart", {})


def _save_cart(session, cart: dict) -> None:
    session["cart"] = cart
    session.modified = True


def product_view(request: HttpRequest) -> HttpResponse:
    q = request.GET.get("q", "").strip()
    products = Product.objects.all().order_by("name")
    if q:
        products = products.filter(name__icontains=q)
    return render(request, "product.html", {"products": products, "q": q})


@login_required(login_url="login")
def cart_view(request: HttpRequest) -> HttpResponse:
    cart = _get_cart(request.session)
    ids = [int(pid) for pid in cart.keys()]
    products = Product.objects.filter(id__in=ids).order_by("name") if ids else []
    items = []
    total = Decimal("0.00")
    by_id = {str(p.id): p for p in products}
    for pid, qty in cart.items():
        p = by_id.get(str(pid))
        if not p:
            continue
        line_total = Decimal(qty) * p.price
        total += line_total
        items.append({"product": p, "qty": qty, "line_total": line_total})
    success = request.GET.get("success") == "1"
    return render(
        request, "cart.html", {"items": items, "total": total, "success": success}
    )


@login_required(login_url="login")
def add_to_cart(request: HttpRequest) -> HttpResponse:
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid method")
    pid = request.POST.get("product_id")
    qty_raw = request.POST.get("qty", "1")
    if not pid:
        return HttpResponseBadRequest("Missing product_id")
    if not Product.objects.filter(id=pid).exists():
        return HttpResponseBadRequest("Invalid product")

    try:
        qty = max(1, int(qty_raw))
    except (TypeError, ValueError):
        qty = 1

    cart = _get_cart(request.session)
    cart[str(pid)] = cart.get(str(pid), 0) + qty
    _save_cart(request.session, cart)
    return redirect(request.POST.get("next") or reverse("cart"))


@login_required(login_url="login")
def update_cart(request: HttpRequest) -> HttpResponse:
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid method")
    pid = request.POST.get("product_id")
    qty = request.POST.get("qty")
    if not pid or qty is None:
        return HttpResponseBadRequest("Missing params")
    try:
        qty = int(qty)
    except ValueError:
        return HttpResponseBadRequest("Invalid qty")
    cart = _get_cart(request.session)
    if qty <= 0:
        cart.pop(str(pid), None)
    else:
        cart[str(pid)] = qty
    _save_cart(request.session, cart)
    return redirect(reverse("cart"))


@login_required(login_url="login")
def remove_from_cart(request: HttpRequest) -> HttpResponse:
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid method")
    pid = request.POST.get("product_id")
    cart = _get_cart(request.session)
    cart.pop(str(pid), None)
    _save_cart(request.session, cart)
    return redirect(reverse("cart"))


@login_required(login_url="login")
@transaction.atomic
def checkout(request: HttpRequest) -> HttpResponse:
    if request.method != "POST":
        return HttpResponseBadRequest("Invalid method")
    cart = _get_cart(request.session)
    if not cart:
        return redirect(reverse("cart"))

    ids = [int(pid) for pid in cart.keys()]
    products = {p.id: p for p in Product.objects.filter(id__in=ids)}
    if not products:
        return redirect(reverse("cart"))

    order = Orders.objects.create(
        username_id=request.user.username,
        date=timezone.now(),
    )

    with connection.cursor() as cur:
        for pid_str, qty in cart.items():
            pid = int(pid_str)
            p = products.get(pid)
            if not p:
                continue
            cur.execute(
                """
                INSERT INTO ORDER_DETAIL (`order`, product, quantity, unit_price)
                VALUES (%s, %s, %s, %s)
                """,
                [order.id, pid, int(qty), str(p.price)],
            )

    _save_cart(request.session, {})
    return redirect(f"{reverse('cart')}?success=1")
