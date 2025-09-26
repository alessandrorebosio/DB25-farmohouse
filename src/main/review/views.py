from django.shortcuts import get_object_or_404, redirect, render
from django.http import Http404, HttpRequest, HttpResponse, HttpResponseForbidden
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.utils import timezone


from users.views import _ensure_datetime
from .models import Review
from service.models import *
from event.models import *
from .forms import ReviewForm

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


@login_required
def event_review_view(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    
    if not EventSubscription.objects.filter(event=event, user_id=request.user.username).exists():
        return HttpResponseForbidden("You did not attend this event.")
    
    review = Review.objects.filter(user_id=request.user.username, event=event).first()
    
    if request.method == "POST":
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            r = form.save(commit=False)
            r.user_id = request.user.username  
            r.event = event
            r.save()
            return redirect("profile")
    else:
        form = ReviewForm(instance=review)
    
    return render(request, "event_review_form.html", {"form": form, "event": event})

@login_required
def service_review_view(request, service_id):
    # Ottieni l'ultima ReservationDetail per questo servizio e utente
    detail = get_object_or_404(
        ReservationDetail.objects.filter(
            service_id=service_id,
            reservation__username_id=request.user.username
        ).order_by('-end_date'),  # Prendi la prenotazione più recente
        end_date__lte=timezone.now()  # Solo prenotazioni concluse
    )
    
    # Verifica che l'utente possa recensire (il filtro sopra già fa questo controllo)
    if not (detail.end_date and _ensure_datetime(detail.end_date) <= timezone.now()):
        return HttpResponseForbidden("Cannot review before end date.")
    
    # Cerca una recensione esistente
    review = Review.objects.filter(
        user_id=request.user.username, 
        service_id=service_id
    ).first()
    
    if request.method == "POST":
        form = ReviewForm(request.POST, instance=review)
        if form.is_valid():
            r = form.save(commit=False)
            r.user_id = request.user.username
            r.service_id = service_id
            r.save()
            return redirect("profile")
    else:
        form = ReviewForm(instance=review)
    
    return render(request, "service_review_form.html", {"form": form, "detail": detail})
