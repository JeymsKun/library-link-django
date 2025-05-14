# myserver/decorators.py
from django.shortcuts import redirect
from functools import wraps

def staff_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        print(f"[Login Attempt - Staff] {request.user}")
        print(f"[Login Authentication - Staff] Authenticated: {request.user.is_authenticated}")
        print(f"[Session ID Created - Staff] {request.session.keys()}")

        if not request.user.is_authenticated:
            print("Decorator: User is not authenticated")
            return redirect('login_staff')

        if not request.session.get('is_staff', False): 
            print("Decorator: Session does not indicate a logged-in user")
            return redirect('login_staff')

        print(f"[System] {request.user} is now authorized to access the website.")
        return view_func(request, *args, **kwargs)
    return wrapper

def user_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        print(f"[Login Attempt - User] {request.user}")
        print(f"[Login Authentication - User] Authenticated: {request.user.is_authenticated}")
        print(f"[Session ID Created - User] {request.session.keys()}")

        if not request.user.is_authenticated:
            print("Decorator: User is not authenticated")
            return redirect('login_user')

        if not request.session.get('is_user', False):
            print("Decorator: Session does not indicate a logged-in user")
            return redirect('login_user')

        print(f"[System] {request.user} is now authorized to access the website.")
        return view_func(request, *args, **kwargs)
    return wrapper
