"""Custom authentication backend bridging app users with Django auth.

Responsibilities:
- Validate credentials against the app-level `User` table (hashed or plain)
- Ensure a mirrored `django.contrib.auth.models.User` exists
- Set `is_staff`/`is_superuser` flags based on ActiveEmployee/Employee role

This file documents the flow similarly to the Event app's detailed view docs.
"""

from typing import Optional

from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User as DjangoUser
from django.contrib.auth.hashers import check_password
from django.db import transaction

from .models import User, ActiveEmployee


class UserBackend(BaseBackend):
    """Authenticate against application-level users and map to Django User.

    SQL (approximate; backend orchestrates via ORM):

    SELECT U.* FROM "USER" U WHERE U."username" = %s LIMIT 1;

    SELECT AE."role"
    FROM "active_employees" AE
    WHERE AE."username" = %s
    LIMIT 1;
    """

    def authenticate(
        self,
        request,
        username: Optional[str] = None,
        password: Optional[str] = None,
        **kwargs
    ) -> Optional[DjangoUser]:
        """Return a Django user if app-level credentials are valid.

        Steps:
        1) Look up app `User` by username
        2) Verify password using Django's hasher; allow legacy plain matches
        3) In a transaction, upsert Django User and sync staff/superuser flags
        4) Keep email in sync and ensure unusable password
        """
        if not username or not password:
            return None

        try:
            u = User.objects.get(username=username)
        except User.DoesNotExist:
            return None

        stored = u.password or ""
        if not (stored and (check_password(password, stored) or stored == password)):
            return None

        with transaction.atomic():
            user, created = DjangoUser.objects.get_or_create(
                username=username,
                defaults={"email": u.email or "", "first_name": "", "last_name": ""},
            )
            ae = ActiveEmployee.objects.filter(username=username).values("role").first()
            if ae:
                user.is_staff = True
                user.is_superuser = (ae.get("role") or "").lower() == "admin"
            else:
                user.is_staff = False
                user.is_superuser = False

            if not user.has_usable_password():
                user.set_unusable_password()

            if u.email and user.email != u.email:
                user.email = u.email

            user.save()

        return user

    def get_user(self, user_id: int) -> Optional[DjangoUser]:
        """Resolve a Django auth user by primary key, or None if missing."""
        try:
            return DjangoUser.objects.get(pk=user_id)
        except DjangoUser.DoesNotExist:
            return None
