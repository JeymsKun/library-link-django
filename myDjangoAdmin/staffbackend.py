# myDjangoAdmin/auth_backends.py
from django.contrib.auth.backends import BaseBackend
from myDjangoAdmin.models import Staff

class StaffBackend(BaseBackend):
    """Authenticate Staff using email and password."""

    def authenticate(self, request, email=None, password=None, **kwargs):
        if email is None or password is None:
            return None

        try:
            staff = Staff.objects.get(email=email)
            if staff.check_password(password) and staff.is_active:
                return staff
        except Staff.DoesNotExist:
            return None

    def get_user(self, user_id):
        try:
            return Staff.objects.get(pk=user_id)
        except Staff.DoesNotExist:
            return None
