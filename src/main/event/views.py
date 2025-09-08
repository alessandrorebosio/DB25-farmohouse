from django.db.models import Q, F, Sum, IntegerField
from django.db.models.functions import Coalesce
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.shortcuts import render, redirect
from django.http import HttpRequest, HttpResponse

from .models import Event


def event_view(request: HttpRequest) -> HttpResponse:
    q = (request.GET.get("q") or "").strip()
    today = timezone.localdate()

    qs = (
        Event.objects.select_related("created_by")
        .filter(event_date__gte=today)
        .annotate(
            taken=Coalesce(
                Sum("subscriptions__participants"), 0, output_field=IntegerField()
            ),
            remaining=F("seats")
            - Coalesce(
                Sum("subscriptions__participants"), 0, output_field=IntegerField()
            ),
        )
        .order_by("event_date", "title")
    )
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(description__icontains=q))

    return render(request, "events.html", {"events": qs, "q": q})
