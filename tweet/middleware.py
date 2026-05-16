from django.shortcuts import redirect
from django.urls import reverse
from django.http import HttpResponse


class UptimeRobotMiddleware:
    """
    Intercepts UptimeRobot health checks and returns a 200 OK response immediately
    to avoid processing the full Django request lifecycle and generating verbose logs.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        if 'UptimeRobot' in user_agent:
            return HttpResponse("OK")
        return self.get_response(request)


class ProfileCompletionMiddleware:
    """
    Ensures that users complete their profile before accessing other parts of the site.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and not request.user.is_staff:
            # If the profile is incomplete, redirect to the setup page,
            if not request.user.profile_is_complete():
                # Define paths that are always accessible, even with an incomplete profile.
                # This prevents redirect loops during login, logout, or profile setup.
                allowed_paths = [
                    reverse('profile_setup'),
                    reverse('account_logout'),
                ]

                # Allow access to all /accounts/ URLs (for login, password reset, etc.)
                is_allowed_path = request.path in allowed_paths or request.path.startswith('/accounts/')

                if not is_allowed_path:
                    return redirect('profile_setup')

        return self.get_response(request)