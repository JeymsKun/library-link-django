from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.utils.timezone import now

class UpdateLastSeenMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            if hasattr(request.user, 'last_seen'):
                request.user.last_seen = now()
                request.user.save(update_fields=["last_seen"])

        response = self.get_response(request)
        return response
        
class AdminAccessMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.path.startswith('/admin/') and (not request.user.is_authenticated or not request.user.is_superuser):
            return HttpResponseForbidden("You do not have permission to access the admin site.")

        response = self.get_response(request)
        return response
