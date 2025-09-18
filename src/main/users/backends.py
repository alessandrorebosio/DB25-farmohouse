from typing import Optional

from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.models import User as DjangoUser
from django.contrib.auth.hashers import check_password
from django.db import transaction

from .models import User, Employee, ActiveEmployee


class UserBackend(BaseBackend):

    def authenticate(
        self,
        request,
        username: Optional[str] = None,
        password: Optional[str] = None,
        **kwargs
    ) -> Optional[DjangoUser]:
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

            # Active employees -> staff + superuser
            if ActiveEmployee.objects.filter(username=username).exists():
                user.is_staff = True
                user.is_superuser = True
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
        try:
            return DjangoUser.objects.get(pk=user_id)
        except DjangoUser.DoesNotExist:
            return None
