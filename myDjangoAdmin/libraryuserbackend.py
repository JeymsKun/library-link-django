# myDjangoAdmin/auth_backends.py
from django.contrib.auth.backends import BaseBackend
from myDjangoAdmin.models import LibraryUser

class LibraryUserBackend(BaseBackend):
    """Authenticate LibraryUser using email and password."""

    def authenticate(self, request, email=None, password=None, **kwargs):
        if email is None or password is None:
            return None

        try:
            library_user = LibraryUser.objects.get(email=email)
            if library_user.check_password(password) and library_user.is_active:
                return library_user
        except LibraryUser.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return LibraryUser.objects.get(pk=user_id)
        except LibraryUser.DoesNotExist:
            return None
