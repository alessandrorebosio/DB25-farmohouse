from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Review


def review_view(request: HttpRequest) -> HttpResponse:
    target = request.GET.get("target", "all")
    service_type = request.GET.get(
        "service_type", ""
    )
    rating_min = request.GET.get("rating_min") or None
    rating_max = request.GET.get("rating_max") or None
    username = request.GET.get("username", "").strip()
    q = request.GET.get("q", "").strip()
    order = request.GET.get(
        "order", "newest"
    )
    page = int(request.GET.get("page", "1"))

    qs = Review.objects.select_related("user", "service", "event")

    if target == "service":
        qs = qs.filter(service__isnull=False)
    elif target == "event":
        qs = qs.filter(event__isnull=False)

    if service_type:
        qs = qs.filter(service__type=service_type)

    if rating_min:
        qs = qs.filter(rating__gte=int(rating_min))
    if rating_max:
        qs = qs.filter(rating__lte=int(rating_max))

    if username:
        qs = qs.filter(user__username__icontains=username)

    if q:
        qs = qs.filter(Q(comment__icontains=q) | Q(event__title__icontains=q))

    ordering_map = {
        "newest": "-created_at",
        "oldest": "created_at",
        "rating_desc": "-rating",
        "rating_asc": "rating",
    }
    qs = qs.order_by(ordering_map.get(order, "-created_at"))

    paginator = Paginator(qs, 10)
    page_obj = paginator.get_page(page)

    params = request.GET.copy()
    params.pop("page", None)
    base_qs = params.urlencode()

    context = {
        "page_obj": page_obj,
        "total": paginator.count,
        "filters": {
            "target": target,
            "service_type": service_type,
            "rating_min": rating_min or "",
            "rating_max": rating_max or "",
            "username": username,
            "q": q,
            "order": order,
            "base_qs": base_qs,
        },
        "service_types": ["RESTAURANT", "POOL", "PLAYGROUND", "ROOM"],
    }
    return render(request, "review.html", context)
