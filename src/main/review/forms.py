"""
Forms per il modello Review.

Uso consigliato nelle view:
    review = Review.objects.filter(user=request.user, event=event).first()
    form = ReviewForm(request.POST or None, instance=review)
    if form.is_valid():
        form.save(user=request.user, event=event)   # oppure service=service

La form gestisce sia create che update. La save accetta parametri opzionali
(user, event, service) per assegnare i campi mancanti prima del salvataggio.
"""

from django import forms
from django.core.exceptions import ValidationError
from .models import Review

# Scelte per il rating, mostrate come radio (5..1)
RATING_CHOICES = [
    (5, "5 — ★★★★★"),
    (4, "4 — ★★★★"),
    (3, "3 — ★★★"),
    (2, "2 — ★★"),
    (1, "1 — ★"),
]


class ReviewForm(forms.ModelForm):
    # sovrascriviamo il campo rating per usare RadioSelect e coercizione a int
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
        help_text="Massimo 2000 caratteri.",
    )

    class Meta:
        model = Review
        fields = ["rating", "comment"]

    def clean_rating(self):
        rating = self.cleaned_data.get("rating")
        # coerce assicura int, ma facciamo un controllo ulteriore
        if rating is None:
            raise ValidationError("Rating mancante.")
        if not (1 <= int(rating) <= 5):
            raise ValidationError("Il rating deve essere un intero compreso tra 1 e 5.")
        return int(rating)

    def clean_comment(self):
        c = self.cleaned_data.get("comment") or ""
        if len(c) > 2000:
            raise ValidationError("Il commento non può superare i 2000 caratteri.")
        return c.strip()

    def save(self, commit=True, user=None, event=None, service=None):
        """
        Save che accetta user/event/service opzionali: utile nelle view per assegnare
        i FK prima del salvataggio.
        Esempio:
            form.save(user=request.user, event=event)
            form.save(user=request.user, service=detail.service)
        """
        instance = super().save(commit=False)

        if user is not None:
            instance.user = user

        # assegna event/service solo se forniti (e non già presenti)
        if event is not None:
            instance.event = event
            instance.service = None  # assicurati che sia coerente: review per event
        if service is not None:
            instance.service = service
            instance.event = None  # assicurati che sia coerente: review per service

        if commit:
            instance.save()
        return instance
