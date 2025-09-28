"""Forms for the Review model.

Recommended usage in a view:
    review = Review.objects.filter(user=request.user, event=event).first()
    form = ReviewForm(request.POST or None, instance=review)
    if form.is_valid():
        form.save(user=request.user, event=event)  # or service=service

This form handles both create and update. The custom save accepts optional
keywords (user, event, service) to assign missing foreign keys before saving.
"""

from typing import Optional, Any

from django import forms
from django.core.exceptions import ValidationError
from .models import Review

# Max length for the optional free-text comment
MAX_COMMENT_LEN: int = 2000

# Rating choices displayed as radio buttons (5..1)
RATING_CHOICES = [
    (5, "5 — ★★★★★"),
    (4, "4 — ★★★★"),
    (3, "3 — ★★★"),
    (2, "2 — ★★"),
    (1, "1 — ★"),
]


class ReviewForm(forms.ModelForm):
    """Form to create or update a Review.

    Fields
    - rating: integer 1..5, rendered as radio buttons.
    - comment: optional free text, trimmed and limited to MAX_COMMENT_LEN.

    Validation
    - clean_rating ensures the value is an int in [1, 5].
    - clean_comment trims whitespace and enforces the size limit.

    Save contract
    - save(commit=True, user=None, event=None, service=None) allows attaching
      foreign keys just-in-time and guarantees mutual exclusivity of event/service.
    """

    rating = forms.TypedChoiceField(
        choices=RATING_CHOICES,
        coerce=int,
        widget=forms.RadioSelect(attrs={"class": "form-check-input"}),
        label="Rating",
        help_text="Valuta da 1 (scarso) a 5 (eccellente).",
        error_messages={"required": "Per favore scegli un punteggio."},
    )

    comment = forms.CharField(
        required=False,
        widget=forms.Textarea(
            attrs={
                "rows": 4,
                "placeholder": "Lascia qui la tua recensione (opzionale)",
                "class": "form-control",
            }
        ),
        label="Commento",
        help_text=f"Massimo {MAX_COMMENT_LEN} caratteri.",
    )

    class Meta:
        model = Review
        fields = ["rating", "comment"]

    def clean_rating(self) -> int:
        """Validate and coerce rating to an int in range [1, 5]."""
        rating = self.cleaned_data.get("rating")
        if rating is None:
            raise ValidationError("Rating mancante.")
        value = int(rating)
        if not (1 <= value <= 5):
            raise ValidationError("Il rating deve essere un intero compreso tra 1 e 5.")
        return value

    def clean_comment(self) -> str:
        """Trim whitespace and enforce MAX_COMMENT_LEN characters."""
        c = (self.cleaned_data.get("comment") or "").strip()
        if len(c) > MAX_COMMENT_LEN:
            raise ValidationError("Il commento non può superare i 2000 caratteri.")
        return c

    def save(
        self,
        commit: bool = True,
        user: Optional[Any] = None,
        event: Optional[Any] = None,
        service: Optional[Any] = None,
    ) -> Review:
        """Custom save supporting optional FK assignment.

        Helpful in views to attach the related target just-in-time.
        Examples:
            form.save(user=request.user, event=event)
            form.save(user=request.user, service=detail.service)
        """
        instance = super().save(commit=False)

        if user is not None:
            instance.user = user

        if event is not None:
            instance.event = event
            instance.service = None
        if service is not None:
            instance.service = service
            instance.event = None

        if commit:
            instance.save()
        return instance
