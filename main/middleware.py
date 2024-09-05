from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings
from django.http import HttpResponseForbidden

class AdminRequiredMiddleware:
    """
    Middleware that ensures the user is an admin before granting access to any view.
    If the user is not authenticated, they are redirected to the login page.
    If authenticated but not an admin, they are shown a 403 Forbidden error.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Bypass middleware for the login page or any other public pages you might have
        if request.path in [reverse('login'), reverse('admin:login')]:  # Allow access to the login page
            return self.get_response(request)

        # If the user is not authenticated, redirect to the login page
        if not request.user.is_authenticated:
            return redirect(f"{reverse('login')}?next={request.path}")

        # If the user is authenticated but not an admin, return a 403 Forbidden response
        if not request.user.is_staff:
            return HttpResponseForbidden('You do not have permission to access this page.')

        # If everything is okay, proceed to the requested view
        return self.get_response(request)
