"""Forms for the User app.

Includes a registration form that validates input and persists data
transactionally, mirroring the documentation style used in the Event app.
"""

from django import forms
from django.db import transaction
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import make_password
from .models import Person, User


class RegisterForm(forms.Form):
    """User registration form with basic personal info and credentials.

    Validation rules:
    - tax_code (CF) must be exactly 16 chars, case-insensitive, stored uppercased
    - username must be unique across app users
    - passwords must match

    Persistence:
    - Creates or reuses a Person (by CF)
    - Creates a User linked to that Person, hashing password with Django
    - Uses an atomic transaction to keep Person/User consistent
    """

    tax_code = forms.CharField(label="Tax Code", max_length=16, min_length=16)
    name = forms.CharField(label="Name", max_length=50)
    surname = forms.CharField(label="Surname", max_length=50)
    phone = forms.CharField(label="Phone", max_length=20, required=False)
    city = forms.CharField(label="City", max_length=50, required=False)
    username = forms.CharField(label="Username", max_length=30)
    email = forms.EmailField(label="Email")
    password1 = forms.CharField(label="Password", widget=forms.PasswordInput)
    password2 = forms.CharField(label="Confirm Password", widget=forms.PasswordInput)

    def clean_tax_code(self):
        """Normalize and validate the Italian CF string length."""
        cf = self.cleaned_data["tax_code"].strip().upper()
        if len(cf) != 16:
            raise ValidationError("Tax code must be 16 characters.")
        return cf

    def clean_username(self):
        """Ensure username is not already taken in the app-level User table."""
        u = self.cleaned_data["username"]
        if User.objects.filter(username=u).exists():
            raise ValidationError("Username already in use.")
        return u

    def clean(self):
        """Cross-field validation for matching passwords."""
        cleaned = super().clean()
        if cleaned.get("password1") and cleaned.get("password2"):
            if cleaned["password1"] != cleaned["password2"]:
                raise ValidationError("Passwords do not match.")
        return cleaned

    def save(self):
        """Persist Person and User records atomically.

        Returns the created `User` instance. Raises ValidationError if the
        form is not valid when invoked.
        """
        if not self.is_valid():
            raise ValidationError("Form must be valid before saving.")

        with transaction.atomic():
            person, created = Person.objects.get_or_create(
                cf=self.cleaned_data["tax_code"],
                defaults={
                    "name": self.cleaned_data["name"],
                    "surname": self.cleaned_data["surname"],
                },
            )

            user = User.objects.create(
                username=self.cleaned_data["username"],
                cf=person,
                password=make_password(self.cleaned_data["password1"]),
                email=self.cleaned_data["email"],
            )

        return user
