# myDjangoAdmin/authentication.py
from django.core.cache import cache
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from myDjangoAdmin.models import LibraryUser
from rest_framework_simplejwt.settings import api_settings

class LibraryUserJWTAuthentication(JWTAuthentication):
    user_id_claim = api_settings.USER_ID_CLAIM 

    def get_user(self, validated_token):
        user_id = validated_token.get(self.user_id_claim)
        if user_id is None:
            raise AuthenticationFailed(f"Token missing expected claim: {self.user_id_claim}")

        cache_key = f'libraryuser_{user_id}'

        user = cache.get(cache_key)
        if user is not None:
            return user

        try:
            user = LibraryUser.objects.get(id=user_id)
        except LibraryUser.DoesNotExist:
            raise AuthenticationFailed('User not found', code='user_not_found')

        cache.set(cache_key, user, timeout=300)

        return user
