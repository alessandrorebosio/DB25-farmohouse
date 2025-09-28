from django import forms


class BookingDateForm(forms.Form):
    """Simple date range form used to filter room availability.

    This form intentionally stays minimal: validation for ordering or
    availability is performed in the view where contextual business rules
    (meal slot, overlaps, capacities) are known.
    """

    start_date = forms.DateField(
        label="Start date",
        help_text="Check-in date.",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
    end_date = forms.DateField(
        label="End date",
        help_text="Check-out date.",
        widget=forms.DateInput(attrs={"type": "date"}),
    )
